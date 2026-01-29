from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import EmbeddingService, RAGService

class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('question')
        if not query:
            return Response({"error": "Question is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Vectorize Question
        query_vector = EmbeddingService.get_embedding(query, task_type="retrieval_query")
        if not query_vector:
            return Response({"error": "Failed to process question"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Retrieve Context (Strict Syllabus Policy)
        # Note: RAGService.get_context strictly queries is_approved=True
        context_chunks = RAGService.get_context(query_vector, top_k=3)

        # 3. Generate Answer
        answer = RAGService.generate_answer(query, context_chunks)
        
        # 4. Prepare Response
        sources = [
            {
                "id": c.id, 
                "source": c.source_url or "Manual Entry", 
                "topic": c.topic.title,
                "preview": c.content[:50] + "..."
            } 
            for c in context_chunks
        ]

        return Response({
            "answer": answer,
            "sources": sources
        })
