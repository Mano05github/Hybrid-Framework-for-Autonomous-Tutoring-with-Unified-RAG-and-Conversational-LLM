"""
concept_graph.py — ConceptNode graph helpers

Provides:
    get_next_concept(user, subject)   → ConceptNode (adaptive)
    get_concept_by_id(concept_id)    → ConceptNode
    get_concept_for_subject_slug(slug) → ConceptNode  (first unlocked)
    build_subject_graph(subject_id)  → list of node dicts for frontend
"""

import logging
from typing import Optional, List, Dict, Any

from django.db.models import Avg

logger = logging.getLogger(__name__)


def get_next_concept(user, subject) -> Optional['ConceptNode']:
    """
    Returns the most appropriate ConceptNode for the user to work on.

    Strategy:
    1. Find concepts the user has NOT yet mastered (mastery < 0.7) in subject.
    2. Among those, pick prerequisites-satisfied nodes with lowest difficulty first.
    3. Fall back to the first active node if all are mastered.
    """
    from ai_engine.pbl.models import ConceptNode, PBLSession

    # All active concepts for this subject
    candidates = ConceptNode.objects.filter(
        topic__subject=subject, is_active=True
    ).prefetch_related('prerequisites')

    if not candidates.exists():
        return None

    # Build set of mastered concept IDs (avg mastery ≥ 0.7 across completed sessions)
    from django.db.models import Avg
    mastered_ids = set(
        PBLSession.objects.filter(
            user=user, status='completed', concept__topic__subject=subject
        ).values('concept_id').annotate(avg_m=Avg('mastery_score'))
        .filter(avg_m__gte=0.7).values_list('concept_id', flat=True)
    )

    # Concepts the user has ever attempted (for difficulty preference)
    attempted_ids = set(
        PBLSession.objects.filter(
            user=user, concept__topic__subject=subject
        ).values_list('concept_id', flat=True)
    )

    # Filter to unmastered candidates whose prerequisites are all mastered
    available = []
    for node in candidates:
        if node.pk in mastered_ids:
            continue
        prereq_ids = set(node.prerequisites.values_list('pk', flat=True))
        if prereq_ids and not prereq_ids.issubset(mastered_ids):
            continue
        available.append(node)

    if not available:
        # All mastered — start again with the hardest
        available = list(candidates.order_by('-difficulty'))

    if not available:
        return None

    # Sort: prefer attempted first (so hints accumulate), then lowest difficulty
    available.sort(key=lambda n: (n.pk not in attempted_ids, n.difficulty))
    return available[0]


def get_concept_by_id(concept_id: int) -> Optional['ConceptNode']:
    from ai_engine.pbl.models import ConceptNode
    try:
        return ConceptNode.objects.select_related('topic__subject').get(pk=concept_id)
    except ConceptNode.DoesNotExist:
        return None


def get_concept_for_subject_slug(slug: str, user=None) -> Optional['ConceptNode']:
    """
    Resolves a subject slug/id string → picks the right ConceptNode.
    slug can be a subject pk (int-like string) or a Subject.name fragment.
    """
    from ai_engine.pbl.models import ConceptNode
    from core.models import Subject

    # Try numeric id first
    subject = None
    try:
        subject = Subject.objects.get(pk=int(slug))
    except (ValueError, Subject.DoesNotExist):
        pass

    # Normalise slug: "python-basics" / "python_basics" → "python basics" for icontains
    normalised = slug.replace('-', ' ').replace('_', ' ')

    # Try name icontains
    if subject is None:
        qs = Subject.objects.filter(name__icontains=normalised)
        if not qs.exists():
            qs = Subject.objects.filter(name__icontains=slug)
        subject = qs.first()

    if subject is None:
        logger.warning('[ConceptGraph] No subject found for slug=%s', slug)
        return None

    if user:
        return get_next_concept(user, subject)

    # No user → return first active node by difficulty
    return ConceptNode.objects.filter(
        topic__subject=subject, is_active=True
    ).order_by('difficulty').first()


def build_subject_graph(subject_id: int) -> List[Dict[str, Any]]:
    """
    Returns a JSON-serialisable list of concept nodes with edges.
    Used by the dashboard concept graph panel.
    """
    from ai_engine.pbl.models import ConceptNode

    nodes = ConceptNode.objects.filter(
        topic__subject_id=subject_id, is_active=True
    ).prefetch_related('prerequisites').select_related('topic')

    result = []
    for node in nodes:
        result.append({
            'id':          node.pk,
            'slug':        node.slug,
            'title':       node.topic.title,
            'difficulty':  node.difficulty,
            'description': node.description,
            'prereqs':     list(node.prerequisites.values_list('pk', flat=True)),
        })
    return result
