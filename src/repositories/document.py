from typing import Optional, Dict, Any, List


from  src.database.rag import (
    get_document as db_get_document,
    list_documents as db_list_documents,
    db_pool,
)











class DocumentRepository:
    async def get(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        return await db_get_document(db_pool.pool, document_id)

    async def list(self, limit: int = 100, offset: int = 0, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List documents with optional filtering."""
        return await db_list_documents(db_pool.pool, limit=limit, offset=offset, metadata_filter=metadata_filter)


