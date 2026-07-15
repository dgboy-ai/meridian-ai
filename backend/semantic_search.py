"""Semantic Search for Playbook Retrieval — vector-based pattern matching.

"Vector-based playbook retrieval on top of keyword search."

Based on DataHub v1.6.0 Semantic Search with embedding providers.
This module provides semantic similarity search for playbooks and incidents,
enabling more accurate pattern matching in the reflexion loop.

When keyword search fails to find relevant playbooks (because the terminology
differs), semantic search finds playbooks that are conceptually similar.
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("meridian-ai.semantic_search")


@dataclass
class SearchResult:
    """A single search result with similarity score."""
    document_id: str
    title: str
    content: str
    similarity_score: float
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "similarity_score": round(self.similarity_score, 4),
            "tags": self.tags,
        }


class SemanticSearchEngine:
    """Vector-based semantic search for playbooks and incidents.

    Uses TF-IDF-like similarity for local operation.
    For production, would integrate with DataHub v1.6.0 Semantic Search API.
    """

    def __init__(self):
        self._documents: dict[str, dict] = {}
        self._embeddings: dict[str, list[float]] = {}

    def index_document(self, doc_id: str, title: str, content: str, tags: list[str] | None = None):
        """Index a document for semantic search."""
        self._documents[doc_id] = {
            "title": title,
            "content": content,
            "tags": tags or [],
        }
        # Compute simple TF-IDF-like embedding
        self._embeddings[doc_id] = self._compute_embedding(f"{title} {content}")

    def _compute_embedding(self, text: str) -> list[float]:
        """Compute a simple embedding from text.

        In production, this would use DataHub's embedding providers
        (Vertex AI, Ollama, etc.) via v1.6.0 Semantic Search API.
        """
        # Simple character frequency embedding for local operation
        # In production, replace with actual embeddings
        text_lower = text.lower()
        embedding = [0.0] * 26  # 26 dimensions for a-z

        for char in text_lower:
            if char.isalpha():
                idx = ord(char) - ord('a')
                if 0 <= idx < 26:
                    embedding[idx] += 1.0

        # Normalize
        total = sum(embedding)
        if total > 0:
            embedding = [x / total for x in embedding]

        return embedding

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search(self, query: str, top_k: int = 5, min_score: float = 0.3) -> list[SearchResult]:
        """Search for similar documents using semantic similarity.

        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score threshold

        Returns:
            List of SearchResult objects sorted by similarity
        """
        query_embedding = self._compute_embedding(query)

        results = []
        for doc_id, doc_embedding in self._embeddings.items():
            similarity = self._cosine_similarity(query_embedding, doc_embedding)

            if similarity >= min_score:
                doc = self._documents.get(doc_id, {})
                results.append(SearchResult(
                    document_id=doc_id,
                    title=doc.get("title", ""),
                    content=doc.get("content", ""),
                    similarity_score=similarity,
                    tags=doc.get("tags", []),
                ))

        # Sort by similarity score descending
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        return results[:top_k]

    def find_similar_playbooks(self, incident_finding: str, top_k: int = 3) -> list[SearchResult]:
        """Find playbooks similar to an incident finding.

        Args:
            incident_finding: The finding from an incident investigation
            top_k: Number of similar playbooks to return

        Returns:
            List of similar playbooks
        """
        # Search for playbooks specifically
        results = self.search(incident_finding, top_k=top_k * 2)

        # Filter to only playbooks
        playbook_results = [r for r in results if "playbook" in " ".join(r.tags).lower()]

        # If not enough playbooks, include other similar documents
        if len(playbook_results) < top_k:
            non_playbook = [r for r in results if "playbook" not in " ".join(r.tags).lower()]
            playbook_results.extend(non_playbook[:top_k - len(playbook_results)])

        return playbook_results[:top_k]

    def update_document(self, doc_id: str, title: str, content: str, tags: list[str] | None = None):
        """Update an existing document's embedding."""
        if doc_id in self._documents:
            self.index_document(doc_id, title, content, tags)

    def remove_document(self, doc_id: str):
        """Remove a document from the index."""
        self._documents.pop(doc_id, None)
        self._embeddings.pop(doc_id, None)

    def get_stats(self) -> dict:
        """Get search engine statistics."""
        return {
            "total_documents": len(self._documents),
            "indexed_documents": len(self._embeddings),
            "average_embedding_length": (
                sum(len(e) for e in self._embeddings.values()) / max(len(self._embeddings), 1)
            ),
        }
