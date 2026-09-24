"""
seed_concept_graph.py
=====================
Seeds ConceptNode rows for every existing Topic in the database.
Creates a slug from the topic title, assigns difficulty 1–3 based on
topic.order, and wires prerequisites from Topic.prerequisites M2M.

Usage:
    cd backend
    python seed_concept_graph.py

Safe to run multiple times — uses get_or_create.
"""

import os
import sys
import django

# -- Bootstrap Django --
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.utils.text import slugify
from core.models import Topic
from ai_engine.pbl.models import ConceptNode


def difficulty_for_order(order: int) -> int:
    """Map topic.order to a difficulty 1–5."""
    if order <= 2:  return 1
    if order <= 5:  return 2
    if order <= 9:  return 3
    if order <= 14: return 4
    return 5


def seed():
    topics = Topic.objects.select_related('subject').prefetch_related('prerequisites')
    created_count = 0
    updated_count = 0

    # First pass — create/update all ConceptNodes
    topic_to_node: dict = {}
    for topic in topics:
        base_slug = slugify(topic.title)[:100]
        slug      = base_slug
        counter   = 1
        while ConceptNode.objects.filter(slug=slug).exclude(topic=topic).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        node, was_created = ConceptNode.objects.get_or_create(
            topic=topic,
            defaults={
                'slug':        slug,
                'description': topic.description or '',
                'difficulty':  difficulty_for_order(topic.order),
                'is_active':   True,
            },
        )
        if not was_created:
            # Ensure slug is set even for pre-existing nodes
            if not node.slug:
                node.slug = slug
                node.save(update_fields=['slug'])
            updated_count += 1
        else:
            created_count += 1

        topic_to_node[topic.pk] = node

    # Second pass — wire prerequisites
    wired = 0
    for topic in topics:
        node = topic_to_node.get(topic.pk)
        if node is None:
            continue
        for prereq_topic in topic.prerequisites.all():
            prereq_node = topic_to_node.get(prereq_topic.pk)
            if prereq_node and prereq_node not in node.prerequisites.all():
                node.prerequisites.add(prereq_node)
                wired += 1

    print(f"ConceptNodes: {created_count} created, {updated_count} already existed.")
    print(f"Prerequisites wired: {wired}")
    print("Seed complete ✅")


if __name__ == '__main__':
    seed()
