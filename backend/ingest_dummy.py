import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.ingestion import IngestionService
from core.models import Topic

def ingest_content():
    try:
        topic = Topic.objects.get(title="Python Basics")
        text = """
        Python lists are mutable sequences, used to store collections of items.
        You can create a list using square brackets [].
        Example: my_list = [1, 2, 3]
        Lists offer methods like append(), remove(), and pop() to modify the content.
        Because they are mutable, you can change items in place.
        """
        
        count = IngestionService.ingest_text(text, topic.id, source_url="Manual Test", is_scraped=False)
        print(f"Ingested {count} chunks for {topic.title}.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ingest_content()
