import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.models import KnowledgeChunk
from core.models import Topic

def approve_topic(topic_name):
    try:
        topic = Topic.objects.get(title=topic_name)
        chunks = KnowledgeChunk.objects.filter(topic=topic, is_approved=False)
        count = chunks.count()
        if count > 0:
            chunks.update(is_approved=True)
            print(f"Approved {count} chunks for topic '{topic.title}'.")
        else:
            print(f"No draft chunks found for topic '{topic.title}'.")
    except Topic.DoesNotExist:
        print(f"Topic '{topic_name}' not found.")

if __name__ == "__main__":
    approve_topic("Algorithms")
