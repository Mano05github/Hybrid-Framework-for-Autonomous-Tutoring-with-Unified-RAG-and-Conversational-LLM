"""
Migration 0003 — Merge + Vision Fields

Merges the two 0002 branches:
  - 0002_gemini_embedding_768d (embedding dimension change)
  - 0002_knowledgechunk_vision_fields (has_diagram + diagram_image_path)

Then adds the vision fields if not already added.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0002_gemini_embedding_768d"),
        ("rag", "0002_knowledgechunk_vision_fields"),
    ]

    operations = []
