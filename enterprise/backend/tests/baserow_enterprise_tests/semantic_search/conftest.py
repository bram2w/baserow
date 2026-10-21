import hashlib
import math
import re
from unittest.mock import patch

from django.test import override_settings

import pytest

from baserow.core.pgvector import DEFAULT_EMBEDDING_DIMENSIONS, try_enable_pgvector


class FakeEmbedder:
    """
    Embeds texts as a bag of words, so that texts sharing words are similar. It
    replaces the embeddings service, which runs a machine learning model.
    """

    def __init__(self):
        self.embedded_texts = []

    def __call__(self, texts):
        self.embedded_texts.extend(texts)
        return [self.embed(text) for text in texts]

    def embed(self, text):
        vector = [0.0] * DEFAULT_EMBEDDING_DIMENSIONS
        for word in re.findall(r"\w+", text.lower()):
            digest = hashlib.md5(word.encode(), usedforsecurity=False).digest()
            vector[int.from_bytes(digest[:4]) % DEFAULT_EMBEDDING_DIMENSIONS] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


@pytest.fixture
def semantic_search_available(enterprise_data_fixture, synced_roles):
    """
    Makes semantic search available and licensed, using the configured embeddings
    service.
    """

    assert try_enable_pgvector(), "pgvector is required to run these tests."
    # The test license is only valid in debug mode.
    with override_settings(DEBUG=True, BASEROW_EMBEDDINGS_API_URL="http://embeddings"):
        enterprise_data_fixture.enable_enterprise()
        yield


@pytest.fixture
def semantic_search(semantic_search_available):
    """
    Makes semantic search available and licensed, with a fake embeddings service.
    """

    embedder = FakeEmbedder()
    with patch(
        "baserow_enterprise.semantic_search.handler.get_embedder",
        return_value=embedder,
    ):
        yield embedder
