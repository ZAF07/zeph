from fastembed import TextEmbedding

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


class FastEmbedEmbedder:
    """Embeds text locally with fastembed and a small BGE model.

    The model is downloaded on first use and kept in fastembed's cache.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        """Load the model.

        Args:
            model_name: The fastembed model to use.
        """
        self._model = TextEmbedding(model_name)

    def embed_passages(self, texts: list[str]) -> list[list[float]]:
        """Embed pieces of Knowledge to be searched later.

        Args:
            texts: The pieces' texts.

        Returns:
            One embedding per text, in the same order.
        """
        return [
            [float(value) for value in vector]
            for vector in self._model.passage_embed(texts)
        ]

    def embed_query(self, text: str) -> list[float]:
        """Embed a message to search Knowledge with.

        Args:
            text: The message.

        Returns:
            Its embedding.
        """
        [vector] = list(self._model.query_embed(text))
        return [float(value) for value in vector]
