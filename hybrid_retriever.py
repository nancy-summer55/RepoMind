import re

import numpy as np
from nltk.stem import PorterStemmer
from rank_bm25 import BM25Okapi


# ============================================================
# Tokenization configuration
# ============================================================

stemmer = PorterStemmer()


STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "how",
    "what",
    "where",
    "when",
    "why",
    "who",
    "does",
    "do",
    "did",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "and",
    "or",
    "this",
    "that",
    "it",
}


# Match identifiers such as:
#
# generate
# from_pretrained
# CausalSelfAttention
# GPT2LMHeadModel
IDENTIFIER_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*|\d+"
)


# ============================================================
# Split code identifier
# ============================================================

def split_identifier(identifier):
    """
    Split Python/code identifiers into meaningful pieces.

    Examples:

    from_pretrained
        ->
    from, pretrained

    CausalSelfAttention
        ->
    Causal, Self, Attention

    GPT2LMHeadModel
        ->
    GPT, 2, LM, Head, Model
    """

    pieces = []

    # First split snake_case
    snake_parts = identifier.split("_")

    for part in snake_parts:

        if not part:
            continue

        # Split CamelCase / PascalCase / acronyms / numbers
        camel_parts = re.findall(
            r"[A-Z]+(?=[A-Z][a-z]|\d|$)"
            r"|[A-Z]?[a-z]+"
            r"|\d+",
            part
        )

        if camel_parts:
            pieces.extend(camel_parts)
        else:
            pieces.append(part)

    return pieces


# ============================================================
# BM25 tokenizer
# ============================================================

def tokenize_for_bm25(text):
    """
    Code-aware tokenizer.

    It keeps:
    - complete identifiers
    - snake_case pieces
    - CamelCase pieces
    - Porter stems

    Example:

    "def generate_text()"

    may produce tokens similar to:

    def
    generate
    gener
    text
    """

    output_tokens = []

    raw_identifiers = IDENTIFIER_PATTERN.findall(
        text
    )

    for identifier in raw_identifiers:

        variants = [
            identifier
        ]

        variants.extend(
            split_identifier(identifier)
        )

        for variant in variants:

            token = variant.lower()

            if not token:
                continue

            if token in STOP_WORDS:
                continue

            if len(token) == 1:
                continue

            # Original normalized token
            output_tokens.append(token)

            # Stemmed token
            stemmed = stemmer.stem(token)

            if (
                stemmed
                and stemmed != token
            ):
                output_tokens.append(
                    stemmed
                )

    return output_tokens


# ============================================================
# Load BM25 corpus from Chroma
# ============================================================

def load_bm25_corpus(collection):
    """
    Reuse the chunks already stored in Chroma.

    No repository re-index is required.
    """

    collection_size = collection.count()

    result = collection.get(
        limit=collection_size,
        include=[
            "documents",
            "metadatas"
        ]
    )

    records = []
    tokenized_corpus = []

    for (
        chunk_id,
        document,
        metadata
    ) in zip(
        result["ids"],
        result["documents"],
        result["metadatas"]
    ):

        if not document:
            continue

        path = metadata.get(
            "path",
            ""
        )

        # Include file path as lexical information.
        searchable_text = (
            f"{path}\n{document}"
        )

        tokens = tokenize_for_bm25(
            searchable_text
        )

        if not tokens:
            continue

        records.append({
            "id": chunk_id,
            "document": document,
            "metadata": metadata
        })

        tokenized_corpus.append(
            tokens
        )

    return records, tokenized_corpus


# ============================================================
# BM25 Search
# ============================================================

def bm25_search(
    collection,
    query,
    top_k=15
):
    """
    Run BM25 lexical retrieval.
    """

    records, tokenized_corpus = (
        load_bm25_corpus(
            collection
        )
    )

    if not records:
        return []

    bm25 = BM25Okapi(
        tokenized_corpus
    )

    query_tokens = tokenize_for_bm25(
        query
    )

    if not query_tokens:
        return []

    scores = bm25.get_scores(
        query_tokens
    )

    ranked_indices = np.argsort(
        scores
    )[::-1]

    search_results = []

    for index in ranked_indices:

        score = float(
            scores[index]
        )

        # Avoid adding arbitrary zero-score documents.
        if score <= 0:
            continue

        record = records[index]

        search_results.append({
            "id": record["id"],
            "document": record["document"],
            "metadata": record["metadata"],
            "bm25_score": score
        })

        if len(search_results) >= top_k:
            break

    return search_results


# ============================================================
# Reciprocal Rank Fusion
# ============================================================

def reciprocal_rank_fusion(
    vector_results,
    bm25_results,
    rrf_k=60
):
    """
    Fuse Vector Search and BM25 rankings.

    RRF score:

        1 / (rrf_k + rank)

    Scores from Vector Search and BM25 are NOT
    directly added together.
    """

    fused = {}

    # --------------------------------------------------------
    # Vector rankings
    # --------------------------------------------------------

    for rank, result in enumerate(
        vector_results,
        start=1
    ):

        chunk_id = result["id"]

        if chunk_id not in fused:

            fused[chunk_id] = {
                "id": chunk_id,
                "document": result[
                    "document"
                ],
                "metadata": result[
                    "metadata"
                ],

                "similarity": result.get(
                    "similarity"
                ),

                "distance": result.get(
                    "distance"
                ),

                "bm25_score": None,

                "vector_rank": None,
                "bm25_rank": None,

                "rrf_score": 0.0
            }

        fused[chunk_id][
            "vector_rank"
        ] = rank

        fused[chunk_id][
            "similarity"
        ] = result.get(
            "similarity"
        )

        fused[chunk_id][
            "distance"
        ] = result.get(
            "distance"
        )

        fused[chunk_id][
            "rrf_score"
        ] += (
            1.0
            / (rrf_k + rank)
        )

    # --------------------------------------------------------
    # BM25 rankings
    # --------------------------------------------------------

    for rank, result in enumerate(
        bm25_results,
        start=1
    ):

        chunk_id = result["id"]

        if chunk_id not in fused:

            fused[chunk_id] = {
                "id": chunk_id,
                "document": result[
                    "document"
                ],
                "metadata": result[
                    "metadata"
                ],

                "similarity": None,
                "distance": None,

                "bm25_score": None,

                "vector_rank": None,
                "bm25_rank": None,

                "rrf_score": 0.0
            }

        fused[chunk_id][
            "bm25_rank"
        ] = rank

        fused[chunk_id][
            "bm25_score"
        ] = result.get(
            "bm25_score"
        )

        fused[chunk_id][
            "rrf_score"
        ] += (
            1.0
            / (rrf_k + rank)
        )

    # --------------------------------------------------------
    # Sort by final RRF score
    # --------------------------------------------------------

    fused_results = list(
        fused.values()
    )

    fused_results.sort(
        key=lambda item: item[
            "rrf_score"
        ],
        reverse=True
    )

    return fused_results