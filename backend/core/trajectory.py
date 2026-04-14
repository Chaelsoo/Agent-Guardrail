import numpy as np
from collections import defaultdict

# Per session: list of embeddings of flagged messages
_session_flagged_embeddings: dict[str, list[np.ndarray]] = defaultdict(list)

FLAG_THRESHOLD = 0.3  # messages scoring above this are "flagged" and tracked


def compute_trajectory_score(session_id: str, msg_embedding: np.ndarray) -> float:
    """
    Returns cosine similarity between current message and the session's
    injection centroid (mean of flagged message embeddings).
    Returns 0.0 if no flagged messages yet.
    """
    flagged = _session_flagged_embeddings.get(session_id, [])
    if not flagged:
        return 0.0
    centroid = np.mean(flagged, axis=0)
    centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
    return float(np.dot(msg_embedding, centroid))


def update_trajectory(session_id: str, msg_embedding: np.ndarray, classifier_score: float):
    """Add embedding to session centroid if message was flagged."""
    if classifier_score > FLAG_THRESHOLD:
        _session_flagged_embeddings[session_id].append(msg_embedding)


def clear_session(session_id: str):
    _session_flagged_embeddings.pop(session_id, None)
