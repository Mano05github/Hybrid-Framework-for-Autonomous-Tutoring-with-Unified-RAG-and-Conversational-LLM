"""
RAG Migration 0001 — Initial KnowledgeChunk table

Creates:
  - pgvector extension (if not exists)
  - rag_knowledgechunk table
  - HNSW index on embedding column (cosine distance)
  - Composite index on (topic_id, is_active, index_version) for fast filtered search
"""

import django.db.models.deletion
import pgvector.django
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        # Enable pgvector extension
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="",  # Never drop the extension on rollback
        ),

        migrations.CreateModel(
            name="KnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(help_text='e.g. "CS", "Math", "Physics"', max_length=50)),
                ("concept_tag", models.CharField(help_text='e.g. "Binary Search"', max_length=100)),
                ("text", models.TextField(help_text="Natural language — THE ONLY FIELD THAT GETS EMBEDDED.")),
                ("chunk_type", models.CharField(
                    choices=[
                        ("definition", "Definition"),
                        ("concept", "Concept / Intuition"),
                        ("rule", "Rule / Law / Formula"),
                        ("procedure", "Procedure / Method"),
                        ("example", "Worked Example"),
                        ("mistake", "Common Mistake"),
                        ("comparison", "Comparison / Edge Case"),
                    ],
                    db_index=True,
                    default="concept",
                    max_length=20,
                )),
                ("difficulty", models.CharField(
                    choices=[("easy", "Easy"), ("medium", "Medium"), ("hard", "Hard")],
                    db_index=True,
                    default="medium",
                    max_length=10,
                )),
                ("source_file", models.CharField(blank=True, max_length=255)),
                ("source_page", models.IntegerField(blank=True, null=True)),
                ("chunk_index", models.IntegerField(default=0)),
                ("formula_latex", models.TextField(blank=True)),
                ("formula_plain", models.TextField(blank=True)),
                ("embedding", pgvector.django.VectorField(dimensions=1536, help_text="OpenAI text-embedding-3-small")),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("index_version", models.CharField(db_index=True, default="v1.0", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("topic", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="knowledge_chunks",
                    to="core.topic",
                )),
                ("parent_chunk", models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name="child_chunks",
                    to="rag.knowledgechunk",
                )),
            ],
            options={
                "verbose_name": "Knowledge Chunk",
                "verbose_name_plural": "Knowledge Chunks",
                "ordering": ["topic", "chunk_index"],
            },
        ),

        # Composite index for filtered retrieval (topic_id + is_active + version)
        migrations.AddIndex(
            model_name="knowledgechunk",
            index=models.Index(
                fields=["topic", "is_active", "index_version"],
                name="rag_topic_active_version_idx",
            ),
        ),

        # HNSW vector index — fast approximate cosine search
        # m=16: connections per node (higher = better recall, more RAM)
        # ef_construction=64: build-time search depth (higher = better quality, slower build)
        migrations.RunSQL(
            sql="""
                CREATE INDEX rag_embedding_hnsw_idx
                ON rag_knowledgechunk
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
            """,
            reverse_sql="DROP INDEX IF EXISTS rag_embedding_hnsw_idx;",
        ),
    ]
