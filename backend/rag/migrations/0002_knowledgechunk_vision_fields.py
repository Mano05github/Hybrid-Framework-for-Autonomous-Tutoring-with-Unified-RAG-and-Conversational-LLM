"""
Migration 0002 — Add vision fields to KnowledgeChunk

Adds:
  - has_diagram (BooleanField): page contained drawings/diagrams
  - diagram_image_path (CharField): path to saved page PNG in media/
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgechunk",
            name="has_diagram",
            field=models.BooleanField(
                default=False,
                help_text="True if this chunk was produced from a page containing diagrams.",
            ),
        ),
        migrations.AddField(
            model_name="knowledgechunk",
            name="diagram_image_path",
            field=models.CharField(
                blank=True,
                max_length=500,
                help_text="Path to the saved PNG of the source page in media/rag_diagrams/.",
            ),
        ),
    ]
