"""
Seed Python Basics subject with 5 topics and ConceptNodes.
Run from the backend/ directory:
    python seed_python_basics.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils.text import slugify
from core.models import Subject, Topic
from ai_engine.pbl.models import ConceptNode


TOPICS = [
    {
        'title': 'Variables and Data Types',
        'order': 1,
        'description': 'Integers, floats, strings, booleans, and variable assignment in Python.',
        'difficulty': 1,
        'concept_desc': "Understanding Python's built-in data types and how to store values in variables.",
    },
    {
        'title': 'Control Flow',
        'order': 2,
        'description': 'if/elif/else statements, comparison operators, and boolean logic.',
        'difficulty': 2,
        'concept_desc': 'Making decisions in code using conditional statements and logical operators.',
    },
    {
        'title': 'Loops',
        'order': 3,
        'description': 'for loops, while loops, range(), break, continue, and nested loops.',
        'difficulty': 2,
        'concept_desc': 'Repeating actions efficiently with Python loop constructs.',
    },
    {
        'title': 'Functions',
        'order': 4,
        'description': 'Defining functions, parameters, return values, scope, and lambda expressions.',
        'difficulty': 3,
        'concept_desc': 'Organising code into reusable blocks with def, arguments, return, and scope.',
    },
    {
        'title': 'Lists and Dictionaries',
        'order': 5,
        'description': 'Creating and manipulating lists, list comprehensions, dictionaries, and common methods.',
        'difficulty': 3,
        'concept_desc': "Working with Python's two most essential collection types for storing and organising data.",
    },
]


def run():
    subject, created = Subject.objects.get_or_create(
        name='Python Basics',
        defaults={'description': 'Foundational Python programming for beginners.'}
    )
    action = 'Created' if created else 'Found'
    print(f"{action} Subject: {subject.name} (id={subject.id})")

    prev_concept = None
    for t in TOPICS:
        topic, t_created = Topic.objects.get_or_create(
            subject=subject,
            title=t['title'],
            defaults={
                'order': t['order'],
                'description': t['description'],
            }
        )
        print(f"  {'Created' if t_created else 'Found'} Topic: {topic.title}")

        slug_base = slugify(f"python-basics-{topic.title}")
        concept, c_created = ConceptNode.objects.get_or_create(
            topic=topic,
            defaults={
                'slug': slug_base,
                'description': t['concept_desc'],
                'difficulty': t['difficulty'],
                'is_active': True,
            }
        )
        # Ensure slug is set if concept already existed without one
        if not concept.slug:
            concept.slug = slug_base
            concept.save(update_fields=['slug'])

        print(f"    {'Created' if c_created else 'Found'} ConceptNode: {concept.slug} (d={concept.difficulty})")

        if prev_concept and c_created:
            concept.prerequisites.add(prev_concept)
            print(f"    └─ prerequisite: {prev_concept.slug}")

        prev_concept = concept

    print('\nDone.')


if __name__ == '__main__':
    run()
