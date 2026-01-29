import os
import django
import sys
from pypdf import PdfReader

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_engine.ingestion import IngestionService
from core.models import Topic, Subject

def ingest_pdf(file_path, topic_name):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    print(f"Processing {file_path} for topic '{topic_name}'...")
    
    try:
        # Create or Get Topic
        # Assuming broad subject for now, user can refine later
        subject, _ = Subject.objects.get_or_create(name="General Reference")
        topic, _ = Topic.objects.get_or_create(
            title=topic_name,
            defaults={'subject': subject, 'order': 99}
        )

        reader = PdfReader(file_path)
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n\n"
        
        print(f"Extracted {len(full_text)} characters.")
        
        # Ingest
        # source_url stores the filename for PDFs
        filename = os.path.basename(file_path)
        count = IngestionService.ingest_text(full_text, topic.id, source_url=f"PDF: {filename}", is_scraped=True)
        
        print(f"Successfully ingested {count} chunks into '{topic.title}' (marked as Draft).")
        
    except Exception as e:
        print(f"Error processing PDF: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ingest_pdf.py <path_to_pdf> <topic_name>")
    else:
        ingest_pdf(sys.argv[1], sys.argv[2])
