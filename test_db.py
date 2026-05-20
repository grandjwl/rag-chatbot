import chromadb
from app.core.config import settings

client = chromadb.HttpClient(
    host=settings.CHROMA_HOST,
    port=settings.CHROMA_PORT,
    ssl=settings.CHROMA_SSL,
)

print("ChromaDB 연결 확인:")
print(client.heartbeat())
print("컬렉션 목록:", client.list_collections())