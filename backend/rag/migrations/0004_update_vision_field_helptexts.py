from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0003_merge_vision_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="knowledgechunk",
            name="has_diagram",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "True if this chunk was produced from a page containing "
                    "diagrams or drawings."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="knowledgechunk",
            name="diagram_image_path",
            field=models.CharField(
                blank=True,
                max_length=500,
                help_text=(
                    "Path to the saved PNG of the source page (in media/rag_diagrams/). "
                    "Used to optionally show the student the original diagram during retrieval."
                ),
            ),
        ),
    ]
