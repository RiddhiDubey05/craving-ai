import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Tuple, Optional

from backend.config import get_settings
from backend.utils.logger import app_logger

settings = get_settings()


class FAISSStore:
    def __init__(self):
        self.index_dir = settings.faiss_index_path
        self.index_file = os.path.join(self.index_dir, "index.faiss")
        self.meta_file = os.path.join(self.index_dir, "metadata.json")
        self.dimension = 1024  # Dimensions of Titan Multimodal Embedding

        self.index = None
        self.metadata: List[Dict[str, Any]] = []

        # Ensure index folder exists
        os.makedirs(self.index_dir, exist_ok=True)
        self.load_index()

    def load_index(self):
        """Load FAISS index and metadata from disk if they exist, otherwise initialize a new index."""
        if os.path.exists(self.index_file) and os.path.exists(self.meta_file):
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.meta_file, "r") as f:
                    self.metadata = json.load(f)
                app_logger.info(
                    f"Successfully loaded FAISS index with {self.index.ntotal} items from {self.index_dir}"
                )
            except Exception as e:
                app_logger.error(f"Failed to load FAISS index: {e}. Reinitializing...")
                self._init_empty_index()
        else:
            app_logger.info("No existing FAISS index found. Initializing empty index.")
            self._init_empty_index()

    def _init_empty_index(self):
        """Initialize an empty FAISS IndexFlatIP (Inner Product) for normalized cosine similarity."""
        # IndexFlatIP uses Inner Product search (which is Cosine Similarity if inputs are L2 normalized)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []
        self.save_index()

    def save_index(self):
        """Save FAISS index and metadata list to disk."""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.meta_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
            app_logger.info(f"Saved FAISS index with {self.index.ntotal} items to disk.")
        except Exception as e:
            app_logger.error(f"Failed to save FAISS index: {e}")

    def add_item(self, embedding: List[float], meta: Dict[str, Any]):
        """Add a single item (embedding + metadata) to the vector store."""
        emb_arr = np.array([embedding], dtype=np.float32)
        
        # Verify dimension
        if emb_arr.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.dimension}, got {emb_arr.shape[1]}"
            )

        # L2 normalization for Inner Product (Cosine) Search
        faiss.normalize_L2(emb_arr)
        
        self.index.add(emb_arr)
        self.metadata.append(meta)
        self.save_index()

    def add_items_batch(self, embeddings: List[List[float]], metadata_list: List[Dict[str, Any]]):
        """Add a batch of items (embeddings + metadata) to the vector store."""
        if len(embeddings) != len(metadata_list):
            raise ValueError("Size mismatch between embeddings and metadata_list")

        emb_arr = np.array(embeddings, dtype=np.float32)
        if emb_arr.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension mismatch. Expected {self.dimension}, got {emb_arr.shape[1]}"
            )

        faiss.normalize_L2(emb_arr)
        self.index.add(emb_arr)
        self.metadata.extend(metadata_list)
        self.save_index()

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        cuisine_filter: Optional[str] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        veg_only: bool = False,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for top_k matches using query embedding.
        Supports post-retrieval filtering for metadata.
        Returns a list of tuples: (metadata, similarity_score).
        """
        if self.index.ntotal == 0:
            return []

        emb_arr = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(emb_arr)

        # Retrieve a larger set of candidates (e.g. 5x top_k) to allow for filtering
        candidate_count = min(self.index.ntotal, max(top_k * 5, 50))
        scores, indices = self.index.search(emb_arr, candidate_count)

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            # FAISS returns -1 for empty slots if requested more than total size
            if idx == -1 or idx >= len(self.metadata):
                continue
                
            meta = self.metadata[idx]
            
            # Post-retrieval filtering
            if cuisine_filter and meta.get("cuisine").lower() != cuisine_filter.lower():
                continue
            if max_price is not None and meta.get("price") > max_price:
                continue
            if min_rating is not None and meta.get("rating") < min_rating:
                continue
            if veg_only and not meta.get("is_veg", False):
                continue

            # Map FAISS similarity score (ranges from -1 to 1 for normalized vectors)
            # Clip between 0 and 1 for presentation
            normalized_score = float(np.clip((score + 1.0) / 2.0, 0.0, 1.0))
            
            results.append((meta, normalized_score))
            if len(results) >= top_k:
                break

        return results

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Get list of all items currently stored."""
        return self.metadata

    def clear(self):
        """Clear all entries in the vector store."""
        self._init_empty_index()


# Singleton instance
faiss_store = FAISSStore()
