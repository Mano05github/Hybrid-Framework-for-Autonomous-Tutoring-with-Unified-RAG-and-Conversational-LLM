import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Topic, Lesson

def seed_lessons():
    try:
        topic = Topic.objects.get(title="Algorithms")
        print(f"Found Topic: {topic.title}")
        
        lessons = [
            "Introduction to Algorithms",
            "Selection Sort",
            "Recursion",
            "Quicksort",
            "Hash Tables",
            "Breadth-First Search",
            "Dijkstra's Algorithm",
            "Greedy Algorithms",
            "Dynamic Programming",
            "K-Nearest Neighbors"
        ]
        
        for i, title in enumerate(lessons):
            lesson, created = Lesson.objects.get_or_create(
                topic=topic,
                title=title,
                defaults={
                    'order': i + 1,
                    'content': f"Content for {title}. Ask the AI to explain this!"
                }
            )
            if created:
                print(f"Created Lesson: {title}")
            else:
                print(f"Lesson exists: {title}")
                
    except Topic.DoesNotExist:
        print("Topic 'Algorithms' not found. Please run ingest_pdf.py first.")

if __name__ == "__main__":
    seed_lessons()
