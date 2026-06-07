# backend/services/rag_qa.py
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import chromadb

class RAGQABot:
    def __init__(self, api_key: str):
        """Initialize RAG Q&A bot with ChromaDB and Gemini API."""
        genai.configure(api_key=api_key)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client()
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def search_chunks(self, question: str, collection_name: str, top_k: int = 3) -> list[str]:
        """Search ChromaDB for chunks similar to the question."""
        try:
            collection = self.chroma_client.get_collection(collection_name)
            query_embedding = self.model.encode([question])[0].tolist()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return results["documents"][0] if results["documents"] else []
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []
    
    def build_context(self, chunks: list[str]) -> str:
        """Combine chunks into a single context string."""
        return "\n\n".join([f"[Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(chunks)])
    
    def ask(self, question: str, collection_name: str) -> dict:
        """Ask a question about a document collection."""
        chunks = self.search_chunks(question, collection_name, top_k=3)
        
        if not chunks:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "sources": [],
                "error": "No chunks retrieved"
            }
        
        context = self.build_context(chunks)
        
        prompt = f"""You are a study assistant. Answer questions based ONLY on the provided document chunks.

If the answer is not in the provided text, say "This information is not in the provided document."
Always cite which chunk(s) your answer came from.
Keep answers concise and clear.

Document chunks:
{context}

Question: {question}

Please answer the question using only the information in the chunks above."""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            answer = response.text
            
            return {
                "question": question,
                "answer": answer,
                "sources": chunks,
                "num_chunks_retrieved": len(chunks)
            }
        
        except Exception as e:
            return {
                "question": question,
                "answer": f"Error calling Gemini API: {str(e)}",
                "sources": chunks,
                "error": str(e)
            }