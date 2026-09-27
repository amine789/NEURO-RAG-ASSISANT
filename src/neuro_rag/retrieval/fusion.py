from collections import defaultdict

from neuro_rag.config import RRF_K


def rrf_fuse(*ranked_lists, k=RRF_K):
    """Reciprocal rank fusion: merge ranked lists of chunk_ids into one ranking.

    Each list adds 1 / (k + rank) to every chunk it contains (rank starts at 1), so a
    chunk ranked well by several retrievers beats one ranked first by only one.
    Uses ranks, not scores, because BM25 scores and cosine similarities aren't comparable.
    Returns [(chunk_id, fused_score), ...], best first.
    """
    scores = defaultdict(float)
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
