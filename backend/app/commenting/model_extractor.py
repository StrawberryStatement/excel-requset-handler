from __future__ import annotations

from backend.app.commenting.schemas import CommentContext, ExtractedCommentVariables


class ModelCommentExtractor:
    """Reserved adapter for internal model-based extraction.

    The public project cannot access the internal model. Implement this in the
    internal network, for example with MiniMax, and keep the interface stable.
    """

    def extract(self, context: CommentContext) -> ExtractedCommentVariables:
        raise NotImplementedError("Implement model extraction in the internal environment.")

