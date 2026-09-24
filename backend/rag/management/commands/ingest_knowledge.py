"""
Django Management Command: ingest_knowledge

Offline knowledge ingestion pipeline.
Runs the full pipeline: Load → Clean → Chunk → Validate → Embed → Insert

Usage:
    python manage.py ingest_knowledge --source path/to/docs/ --topic-id 1 --subject CS
    python manage.py ingest_knowledge --source docs/ --topic-id 2 --subject Math --version v1.1 --dry-run
    python manage.py ingest_knowledge --source docs/ --topic-id 1 --subject CS --show-chunks
"""

from django.core.management.base import BaseCommand, CommandError
from rag.ingestion import IngestionPipeline


class Command(BaseCommand):
    help = "Ingest educational documents into the RAG knowledge base."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            help="Path to directory containing PDF, PPTX, or Markdown files.",
        )
        parser.add_argument(
            "--topic-id",
            type=int,
            required=True,
            help="Django Topic.id that this content belongs to.",
        )
        parser.add_argument(
            "--subject",
            required=True,
            help='Subject label, e.g. "CS", "Math", "Physics".',
        )
        parser.add_argument(
            "--index-version",
            default="v2.0",
            help='Index version string (default: v2.0). Must match embedding model lock.',
        )
        parser.add_argument(
            "--concept-tag",
            default="",
            help="Optional concept tag override. If empty, uses filename as tag.",
        )
        parser.add_argument(
            "--difficulty",
            choices=["easy", "medium", "hard"],
            default="medium",
            help="Default difficulty for all chunks in this source (default: medium).",
        )
        parser.add_argument(
            "--topics-file",
            default="",
            help=(
                "Path to a JSON file defining topic hierarchy for this PDF. "
                "Format: [{\"name\": \"Topic\", \"subtopics\": [\"Sub1\", \"Sub2\"]}]. "
                "When provided, uses topic-guided chunking instead of heuristic splitting."
            ),
        )
        parser.add_argument(
            "--no-vision",
            action="store_true",
            default=False,
            help="Skip vision scan entirely (use for structured text PDFs with no handwriting).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Chunk + validate without inserting into DB. Useful for previewing.",
        )
        parser.add_argument(
            "--show-chunks",
            action="store_true",
            default=False,
            help="Print the first 5 valid chunks to stdout for inspection.",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n[RAG] Ingestion Pipeline Starting...\n"))

        source     = options["source"]
        topic_id   = options["topic_id"]
        subject    = options["subject"]
        version    = options["index_version"]
        concept    = options.get("concept_tag", "")
        difficulty = options["difficulty"]
        dry_run    = options["dry_run"]
        show_chunks = options["show_chunks"]
        topics_file = options.get("topics_file", "")
        no_vision   = options.get("no_vision", False)

        if dry_run:
            self.stdout.write(self.style.WARNING("  [!] DRY RUN MODE -- No DB writes will happen.\n"))

        self.stdout.write(f"  Source:      {source}")
        self.stdout.write(f"  Topic ID:    {topic_id}")
        self.stdout.write(f"  Subject:     {subject}")
        self.stdout.write(f"  Version:     {version}")
        self.stdout.write(f"  Difficulty:  {difficulty}\n")

        try:
            pipeline = IngestionPipeline(dry_run=dry_run, show_chunks=show_chunks, use_vision=not no_vision)
            stats = pipeline.run(
                source_dir=source,
                topic_id=topic_id,
                subject=subject,
                index_version=version,
                concept_tag=concept,
                difficulty=difficulty,
                topics_file=topics_file,
            )
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Ingestion failed: {e}")

        # ── Results summary ──────────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS("\n[OK] Ingestion Complete\n"))
        self.stdout.write(f"  Files processed:    {stats['files_processed']}")
        self.stdout.write(f"  Chunks produced:    {stats['chunks_produced']}")
        self.stdout.write(f"  Chunks validated:   {stats['chunks_validated']}")
        self.stdout.write(f"  Chunks inserted:    {stats['chunks_inserted']}")
        self.stdout.write(f"  Chunks skipped:     {stats['chunks_skipped']}")
        if "elapsed_s" in stats:
            self.stdout.write(f"  Time elapsed:       {stats['elapsed_s']:.1f}s")

        if not dry_run and stats["chunks_inserted"] > 0:
            self.stdout.write(self.style.SUCCESS(
                f"\n  [+] Knowledge base updated. "
                f"Topic {topic_id} now has {stats['chunks_inserted']} active chunks (version={version})."
            ))
        elif dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n  DRY RUN complete. Re-run without --dry-run to insert chunks.\n"
            ))
