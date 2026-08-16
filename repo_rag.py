import argparse
import os
import re
import sys
from pathlib import Path

import chromadb
import numpy as np

from dotenv import load_dotenv
from nltk.stem import PorterStemmer
from openai import OpenAI
from rank_bm25 import BM25Okapi
from sentence_transformers import (
    SentenceTransformer,
    CrossEncoder,
)

from repo_loader import load_repository
from chunker import split_documents
from ast_chunker import split_documents_ast

# ============================================================
# Project Paths
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# Configuration
# ============================================================

COLLECTION_NAME = "repomind"

CHROMA_PATH = str(
    BASE_DIR / "chroma_db"
)

EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "jinaai/jina-embeddings-v2-base-code"
)

# 如果 .env 中已经配置 DEEPSEEK_MODEL，
# 会优先使用 .env 中的值。
DEEPSEEK_MODEL = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-chat"
)


# ============================================================
# Retrieval Configuration
# ============================================================

DEFAULT_TOP_K = 5

# top_k = 5 时：
#
# Vector Top-15
# BM25   Top-15
#
CANDIDATE_MULTIPLIER = 3

# Reciprocal Rank Fusion constant
RRF_K = 60

# Overlapping chunk dedup threshold
DEDUP_OVERLAP_THRESHOLD = 0.30


# ============================================================
# Code-aware Reranker Configuration
# ============================================================

RERANKER_MODEL_NAME = (
    "NamanAgnih0tri/code-reranker-miniLM-staqc"
)

# RRF 排名前 15 的候选交给 Reranker
RERANK_CANDIDATE_K = 15

# 使用较小 batch 以降低内存压力。
RERANK_BATCH_SIZE = 4




# ============================================================
# Console Encoding
# ============================================================

def configure_console_encoding():
    """
    Avoid Windows GBK encoding errors when repository
    content contains Unicode characters.
    """

    for stream in (
        sys.stdout,
        sys.stderr,
    ):

        if hasattr(
            stream,
            "reconfigure"
        ):

            try:

                stream.reconfigure(
                    encoding="utf-8",
                    errors="replace"
                )

            except Exception:

                pass


# ============================================================
# Load Embedding Model
# ============================================================

print(
    "Loading embedding model..."
)

if EMBEDDING_MODEL_NAME == "jinaai/jina-embeddings-v2-base-code":

    # Minimal compatibility shim:
    # jina-embeddings-v2-base-code ships a custom modeling_bert.py that
    # imports `find_pruneable_heads_and_indices`, which was removed in
    # transformers>=5. Re-expose the legacy helper before loading.
    import torch
    import transformers.pytorch_utils as _pytorch_utils

    if not hasattr(_pytorch_utils, "find_pruneable_heads_and_indices"):

        def find_pruneable_heads_and_indices(
            heads,
            n_heads,
            head_size,
            already_pruned_heads
        ):
            mask = torch.ones(n_heads, head_size)
            heads = set(heads) - already_pruned_heads
            if len(heads) == 0:
                return heads, torch.zeros(0, 0).long()
            for head in heads:
                mask[head] = 0
            mask = mask.view(-1).contiguous().eq(1)
            index = torch.arange(len(mask))[mask].long()
            return heads, index

        _pytorch_utils.find_pruneable_heads_and_indices = (
            find_pruneable_heads_and_indices
        )

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME,
        trust_remote_code=True
    )

else:

    embedding_model = SentenceTransformer(
        EMBEDDING_MODEL_NAME
    )

print(
    "Embedding model loaded."
)


# ============================================================
# Lazy-loaded Code Reranker
# ============================================================

_reranker_model = None


def get_reranker_model():
    """
    Load Code Reranker only when an ask request
    actually needs reranking.

    This avoids loading the 0.6B reranker when
    running only the index command.
    """

    global _reranker_model

    if _reranker_model is None:

        print(
            "\nLoading Python code reranker..."
        )

        _reranker_model = CrossEncoder(
            RERANKER_MODEL_NAME
        )

        print(
            "Python code reranker loaded."
        )

    return _reranker_model


# ============================================================
# Chroma Persistent Client
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# ============================================================
# Create Clean Collection
# ============================================================

def create_clean_collection():
    """
    Delete old collection if it exists and
    recreate a cosine-distance Chroma collection.
    """

    try:

        chroma_client.delete_collection(
            name=COLLECTION_NAME
        )

        print(
            "Old index found. "
            "Deleting old collection..."
        )

    except Exception:

        pass

    collection = (
        chroma_client.create_collection(

            name=COLLECTION_NAME,

            configuration={
                "hnsw": {
                    "space": "cosine"
                }
            }
        )
    )

    return collection


# ============================================================
# Index Repository
# ============================================================

def index_repository(
    repo_path,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="fixed"
):
    """
    Repository
        ↓
    Loader
        ↓
    Chunking
        ↓
    Embedding
        ↓
    Chroma
    """

    print(
        "\n"
        + "=" * 70
    )

    print(
        "LOADING REPOSITORY"
    )

    print(
        "=" * 70
    )

    documents = load_repository(
        repo_path
    )

    print(
        f"Files loaded: "
        f"{len(documents)}"
    )

    if not documents:

        raise ValueError(
            "No supported .py or .md files were found."
        )

    # --------------------------------------------------------
    # Chunking
    # --------------------------------------------------------

    print(
        "\nCreating chunks..."
    )

    if chunk_strategy == "ast":

        chunks = split_documents_ast(
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    else:

        chunks = split_documents(
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )


    print(
        f"Chunks created: "
        f"{len(chunks)}"
    )

    if not chunks:

        raise ValueError(
            "No chunks were created."
        )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "SAMPLE CHUNKS"
    )

    print(
        "=" * 70
    )

    for chunk in chunks[:3]:

        metadata = (
            chunk["metadata"]
        )

        print(
            f"\nFile: "
            f"{metadata['path']}"
        )

        print(
            f"Lines: "
            f"{metadata['start_line']}"
            f"-"
            f"{metadata['end_line']}"
        )

        print(
            "\nContent:"
        )

        print(
            chunk["content"][:500]
        )

        if (
            len(
                chunk["content"]
            )
            > 500
        ):

            print("...")

        print(
            "-" * 70
        )

    # --------------------------------------------------------
    # Embedding
    # --------------------------------------------------------

    print(
        "\nGenerating embeddings..."
    )

    texts = [
    chunk.get(
        "index_text",
        chunk["content"]
    )
    for chunk in chunks
    ]

    embeddings = (
        embedding_model.encode(

            texts,

            batch_size=32,

            show_progress_bar=True
        )
    )

    print(
        f"Embedding shape: "
        f"{embeddings.shape}"
    )

    # --------------------------------------------------------
    # Chroma
    # --------------------------------------------------------

    collection = (
        create_clean_collection()
    )

    batch_size = 128

    print(
        "\nSaving chunks to Chroma..."
    )

    for start in range(
        0,
        len(chunks),
        batch_size
    ):

        end = min(

            start + batch_size,

            len(chunks)
        )

        batch_chunks = (
            chunks[start:end]
        )

        collection.add(

            ids=[
                chunk["id"]

                for chunk
                in batch_chunks
            ],

            documents=[
                chunk["content"]

                for chunk
                in batch_chunks
            ],

            metadatas=[
                chunk["metadata"]

                for chunk
                in batch_chunks
            ],

            embeddings=embeddings[
                start:end
            ].tolist()
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "INDEX COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Files indexed: "
        f"{len(documents)}"
    )

    print(
        f"Chunks indexed: "
        f"{collection.count()}"
    )


# ============================================================
# Get Collection
# ============================================================

def get_collection():

    try:

        return (
            chroma_client
            .get_collection(
                name=COLLECTION_NAME
            )
        )

    except Exception as error:

        raise RuntimeError(
            "RepoMind index was not found.\n"
            "Run the index command first."
        ) from error


# ============================================================
# Vector Search
# ============================================================

def vector_search_candidates(
    query,
    top_k=15
):
    """
    Raw semantic retrieval.

    No deduplication or reranking occurs here.
    """

    collection = (
        get_collection()
    )

    collection_size = (
        collection.count()
    )

    if collection_size == 0:

        return []

    top_k = min(
        top_k,
        collection_size
    )

    query_embedding = (
        embedding_model.encode(
            query
        )
    )

    results = collection.query(

        query_embeddings=[
            query_embedding.tolist()
        ],

        n_results=top_k,

        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    search_results = []

    for i in range(
        len(
            results[
                "documents"
            ][0]
        )
    ):

        chunk_id = (
            results[
                "ids"
            ][0][i]
        )

        document = (
            results[
                "documents"
            ][0][i]
        )

        metadata = (
            results[
                "metadatas"
            ][0][i]
        )

        distance = (
            results[
                "distances"
            ][0][i]
        )

        similarity = (
            1 - distance
        )

        search_results.append({

            "id":
                chunk_id,

            "document":
                document,

            "metadata":
                metadata,

            "distance":
                distance,

            "similarity":
                similarity
        })

    return search_results


# ============================================================
# BM25 Tokenizer
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


IDENTIFIER_PATTERN = re.compile(
    r"[A-Za-z_][A-Za-z0-9_]*|\d+"
)


# ============================================================
# Split Identifier
# ============================================================

def split_identifier(
    identifier
):
    """
    Examples:

    from_pretrained
        ->
    from
    pretrained

    CausalSelfAttention
        ->
    Causal
    Self
    Attention

    GPT2LMHeadModel
        ->
    GPT
    2
    LM
    Head
    Model
    """

    pieces = []

    snake_parts = (
        identifier.split("_")
    )

    for part in snake_parts:

        if not part:
            continue

        camel_parts = re.findall(

            r"[A-Z]+(?=[A-Z][a-z]|\d|$)"
            r"|[A-Z]?[a-z]+"
            r"|\d+",

            part
        )

        if camel_parts:

            pieces.extend(
                camel_parts
            )

        else:

            pieces.append(
                part
            )

    return pieces


# ============================================================
# BM25 Tokenization
# ============================================================

def tokenize_for_bm25(
    text
):
    """
    IMPORTANT:

    This intentionally preserves the BM25 tokenizer
    used in the successful Hybrid evaluation.

    Do NOT deduplicate variants here, because that
    would alter BM25 scores and RRF rankings.

    Keeps:

    - original identifier
    - snake_case components
    - CamelCase components
    - Porter stems
    """

    output_tokens = []

    identifiers = (
        IDENTIFIER_PATTERN.findall(
            text
        )
    )

    for identifier in identifiers:

        variants = [
            identifier
        ]

        variants.extend(
            split_identifier(
                identifier
            )
        )

        # IMPORTANT:
        #
        # Do NOT use:
        #
        # variants = list(dict.fromkeys(variants))
        #
        # because previous Hybrid baseline did not
        # perform this deduplication.

        for variant in variants:

            token = (
                variant
                .lower()
                .strip()
            )

            if not token:
                continue

            if token in STOP_WORDS:
                continue

            if len(token) == 1:
                continue

            output_tokens.append(
                token
            )

            stemmed = (
                stemmer.stem(
                    token
                )
            )

            if (
                stemmed
                and
                stemmed != token
            ):

                output_tokens.append(
                    stemmed
                )

    return output_tokens


# ============================================================
# Load BM25 Corpus
# ============================================================

def load_bm25_corpus(
    collection
):
    """
    BM25 uses the exact same chunks stored
    in Chroma.
    """

    collection_size = (
        collection.count()
    )

    if collection_size == 0:

        return [], []

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

        symbol_name = metadata.get(
            "symbol_name",
            ""
        )

        qualified_name = metadata.get(
            "qualified_name",
            ""
        )

        searchable_text = (
            f"{path}\n"
            f"{symbol_name}\n"
            f"{qualified_name}\n"
            f"{document}"
        )

        tokens = (
            tokenize_for_bm25(
                searchable_text
            )
        )

        if not tokens:
            continue

        records.append({

            "id":
                chunk_id,

            "document":
                document,

            "metadata":
                metadata
        })

        tokenized_corpus.append(
            tokens
        )

    return (
        records,
        tokenized_corpus
    )


# ============================================================
# BM25 Search
# ============================================================

def bm25_search(
    collection,
    query,
    top_k=15
):
    """
    Lexical retrieval using BM25.
    """

    (
        records,
        tokenized_corpus

    ) = load_bm25_corpus(
        collection
    )

    if not records:

        return []

    bm25 = BM25Okapi(
        tokenized_corpus
    )

    query_tokens = (
        tokenize_for_bm25(
            query
        )
    )

    if not query_tokens:

        return []

    scores = (
        bm25.get_scores(
            query_tokens
        )
    )

    ranked_indices = (
        np.argsort(
            scores
        )[::-1]
    )

    search_results = []

    for index in ranked_indices:

        score = float(
            scores[index]
        )

        if score <= 0:
            continue

        record = (
            records[index]
        )

        search_results.append({

            "id":
                record["id"],

            "document":
                record["document"],

            "metadata":
                record["metadata"],

            "bm25_score":
                score
        })

        if (
            len(search_results)
            >= top_k
        ):

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
    Combine Vector and BM25 rankings.

    RRF score:

        1 / (k + vector_rank)
        +
        1 / (k + bm25_rank)
    """

    fused = {}

    # --------------------------------------------------------
    # Vector
    # --------------------------------------------------------

    for rank, result in enumerate(
        vector_results,
        start=1
    ):

        chunk_id = (
            result["id"]
        )

        if chunk_id not in fused:

            fused[chunk_id] = {

                "id":
                    chunk_id,

                "document":
                    result["document"],

                "metadata":
                    result["metadata"],

                "similarity":
                    result.get(
                        "similarity"
                    ),

                "distance":
                    result.get(
                        "distance"
                    ),

                "bm25_score":
                    None,

                "vector_rank":
                    None,

                "bm25_rank":
                    None,

                "rrf_score":
                    0.0
            }

        fused[
            chunk_id
        ][
            "vector_rank"
        ] = rank

        fused[
            chunk_id
        ][
            "similarity"
        ] = result.get(
            "similarity"
        )

        fused[
            chunk_id
        ][
            "distance"
        ] = result.get(
            "distance"
        )

        fused[
            chunk_id
        ][
            "rrf_score"
        ] += (
            1.0
            /
            (
                rrf_k
                + rank
            )
        )

    # --------------------------------------------------------
    # BM25
    # --------------------------------------------------------

    for rank, result in enumerate(
        bm25_results,
        start=1
    ):

        chunk_id = (
            result["id"]
        )

        if chunk_id not in fused:

            fused[chunk_id] = {

                "id":
                    chunk_id,

                "document":
                    result["document"],

                "metadata":
                    result["metadata"],

                "similarity":
                    None,

                "distance":
                    None,

                "bm25_score":
                    None,

                "vector_rank":
                    None,

                "bm25_rank":
                    None,

                "rrf_score":
                    0.0
            }

        fused[
            chunk_id
        ][
            "bm25_rank"
        ] = rank

        fused[
            chunk_id
        ][
            "bm25_score"
        ] = result.get(
            "bm25_score"
        )

        fused[
            chunk_id
        ][
            "rrf_score"
        ] += (
            1.0
            /
            (
                rrf_k
                + rank
            )
        )

    fused_results = list(
        fused.values()
    )

    fused_results.sort(

        key=lambda item:
            item[
                "rrf_score"
            ],

        reverse=True
    )

    # Debug metadata only: record the fused rank after sorting.
    # Does not change ordering, scores, or retrieval results.
    for rank, result in enumerate(
        fused_results,
        start=1
    ):
        result["rrf_rank"] = rank

    return fused_results


# ============================================================
# Python Code Reranker
# ============================================================

def rerank_candidates(
    query,
    candidates
):
    """
    Rerank RRF candidates with Code Reranker.

    Input:

        query
        +
        repository chunk

    The reranker receives the RepoMind-specific code
    retrieval instruction automatically through
    CrossEncoder prompts.
    """

    if not candidates:

        return []

    model = (
        get_reranker_model()
    )

    pairs = [

        (
            query,
            candidate[
                "document"
            ]
        )

        for candidate
        in candidates
    ]

    # Code Reranker outputs raw ranking scores.
    # We deliberately do NOT apply sigmoid because
    # only relative ranking matters in this experiment.
    scores = model.predict(

        pairs,

        batch_size=
            RERANK_BATCH_SIZE,

        show_progress_bar=False
    )

    scores = (
        np.asarray(
            scores
        )
        .reshape(-1)
    )

    reranked_results = []

    for (
        rrf_rank,
        candidate,
        score

    ) in zip(

        range(
            1,
            len(candidates) + 1
        ),

        candidates,

        scores
    ):

        result = (
            candidate.copy()
        )

        result[
            "rrf_rank"
        ] = rrf_rank

        result[
            "rerank_score"
        ] = float(
            score
        )

        reranked_results.append(
            result
        )

    reranked_results.sort(

        key=lambda item:
            item[
                "rerank_score"
            ],

        reverse=True
    )

    for rank, result in enumerate(
        reranked_results,
        start=1
    ):

        result[
            "rerank_rank"
        ] = rank

    return reranked_results


# ============================================================
# Line Overlap
# ============================================================

def calculate_line_overlap_ratio(
    metadata_a,
    metadata_b
):
    """
    Two chunks can only be considered overlapping
    duplicates when they come from the same file.
    """

    if (
        metadata_a["path"]
        !=
        metadata_b["path"]
    ):

        return 0.0

    start_a = (
        metadata_a[
            "start_line"
        ]
    )

    end_a = (
        metadata_a[
            "end_line"
        ]
    )

    start_b = (
        metadata_b[
            "start_line"
        ]
    )

    end_b = (
        metadata_b[
            "end_line"
        ]
    )

    overlap_start = max(
        start_a,
        start_b
    )

    overlap_end = min(
        end_a,
        end_b
    )

    if (
        overlap_end
        <
        overlap_start
    ):

        return 0.0

    overlap_lines = (
        overlap_end
        - overlap_start
        + 1
    )

    length_a = (
        end_a
        - start_a
        + 1
    )

    length_b = (
        end_b
        - start_b
        + 1
    )

    smaller_length = min(
        length_a,
        length_b
    )

    if smaller_length <= 0:

        return 0.0

    return (
        overlap_lines
        / smaller_length
    )


# ============================================================
# Deduplication
# ============================================================

def deduplicate_search_results(
    search_results,
    top_k=5,
    overlap_threshold=0.30
):
    """
    Remove highly overlapping chunks while
    preserving reranker ranking order.
    """

    selected_results = []

    for candidate in search_results:

        is_duplicate = False

        candidate_metadata = (
            candidate[
                "metadata"
            ]
        )

        for selected in (
            selected_results
        ):

            selected_metadata = (
                selected[
                    "metadata"
                ]
            )

            overlap_ratio = (
                calculate_line_overlap_ratio(

                    candidate_metadata,

                    selected_metadata
                )
            )

            if (
                overlap_ratio
                >=
                overlap_threshold
            ):

                is_duplicate = True

                print(
                    "\n[Dedup] Removed "
                    "overlapping chunk:"
                )

                print(
                    f"  "
                    f"{candidate_metadata['path']} "
                    f"lines "
                    f"{candidate_metadata['start_line']}"
                    f"-"
                    f"{candidate_metadata['end_line']}"
                )

                print(
                    f"  overlap ratio: "
                    f"{overlap_ratio:.2f}"
                )

                break

        if not is_duplicate:

            selected_results.append(
                candidate
            )

        if (
            len(selected_results)
            >= top_k
        ):

            break

    return selected_results


# ============================================================
# Hybrid + Code Reranker Search
# ============================================================

def hybrid_search(
    query,
    top_k=5
):
    """
    Query
        │
        ├──────────────┐
        ▼              ▼
    Vector            BM25
    Top-15            Top-15
        │              │
        └──────┬───────┘
               ▼
              RRF
               ▼
          RRF Top-15
               ▼
       Code Reranker
               ▼
             Dedup
               ▼
           Final Top-K
    """

    collection = (
        get_collection()
    )

    collection_size = (
        collection.count()
    )

    if collection_size == 0:

        return []

    candidate_k = (
        top_k
        *
        CANDIDATE_MULTIPLIER
    )

    candidate_k = min(

        candidate_k,

        collection_size
    )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "HYBRID RETRIEVAL"
    )

    print(
        "=" * 70
    )

    print(
        f"Vector candidates: "
        f"{candidate_k}"
    )

    print(
        f"BM25 candidates: "
        f"{candidate_k}"
    )

    # --------------------------------------------------------
    # Vector Search
    # --------------------------------------------------------

    vector_results = (
        vector_search_candidates(

            query=query,

            top_k=candidate_k
        )
    )

    # --------------------------------------------------------
    # BM25 Search
    # --------------------------------------------------------

    bm25_results = (
        bm25_search(

            collection=collection,

            query=query,

            top_k=candidate_k
        )
    )

    # --------------------------------------------------------
    # Vector Debug
    # --------------------------------------------------------

    print(
        "\nVECTOR TOP RESULTS"
    )

    for rank, result in enumerate(
        vector_results[:5],
        start=1
    ):

        metadata = (
            result["metadata"]
        )

        print(

            f"V#{rank} "

            f"{metadata['path']} "

            f"{metadata['start_line']}"
            f"-"
            f"{metadata['end_line']} "

            f"sim="
            f"{result['similarity']:.4f}"
        )

    # --------------------------------------------------------
    # BM25 Debug
    # --------------------------------------------------------

    print(
        "\nBM25 TOP RESULTS"
    )

    for rank, result in enumerate(
        bm25_results[:5],
        start=1
    ):

        metadata = (
            result["metadata"]
        )

        print(

            f"B#{rank} "

            f"{metadata['path']} "

            f"{metadata['start_line']}"
            f"-"
            f"{metadata['end_line']} "

            f"score="
            f"{result['bm25_score']:.4f}"
        )

    # --------------------------------------------------------
    # RRF
    # --------------------------------------------------------

    fused_results = (
        reciprocal_rank_fusion(

            vector_results=
                vector_results,

            bm25_results=
                bm25_results,

            rrf_k=
                RRF_K
        )
    )

    print(
        "\nRRF FUSED CANDIDATES"
    )

    for rank, result in enumerate(
        fused_results[:10],
        start=1
    ):

        metadata = (
            result["metadata"]
        )

        print(

            f"RRF#{rank} "

            f"{metadata['path']} "

            f"{metadata['start_line']}"
            f"-"
            f"{metadata['end_line']} "

            f"vector_rank="
            f"{result['vector_rank']} "

            f"bm25_rank="
            f"{result['bm25_rank']} "

            f"rrf="
            f"{result['rrf_score']:.6f}"
        )

    # --------------------------------------------------------
    # Dedup AFTER RRF
    # --------------------------------------------------------

    final_results = (
        deduplicate_search_results(

            search_results=
                fused_results,

            top_k=
                top_k,

            overlap_threshold=
                DEDUP_OVERLAP_THRESHOLD
        )
    )

    print(
        f"\nRRF candidates: "
        f"{len(fused_results)}"
    )

    print(
        f"Final results after dedup: "
        f"{len(final_results)}"
    )

    return final_results


# ============================================================
# Build LLM Context
# ============================================================

def build_context(
    search_results
):
    """
    Turn final retrieval results into
    grounded DeepSeek context.
    """

    context_parts = []

    for i, result in enumerate(
        search_results,
        start=1
    ):

        metadata = (
            result["metadata"]
        )

        path = (
            metadata["path"]
        )

        start_line = (
            metadata[
                "start_line"
            ]
        )

        end_line = (
            metadata[
                "end_line"
            ]
        )

        document = (
            result["document"]
        )

        context_part = f"""
[Source {i}]
File: {path}
Lines: {start_line}-{end_line}

{document}
"""

        context_parts.append(
            context_part.strip()
        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# DeepSeek Client
# ============================================================

def get_deepseek_client():

    api_key = os.getenv(
        "DEEPSEEK_API_KEY"
    )

    if not api_key:

        raise ValueError(
            "DEEPSEEK_API_KEY was not found.\n"
            "Check your .env file."
        )

    return OpenAI(

        api_key=
            api_key,

        base_url=
            "https://api.deepseek.com"
    )


# ============================================================
# Generation
# ============================================================

def generate_answer(
    question,
    search_results
):
    """
    Generate grounded answer from the
    final reranked repository context.
    """

    print(
        "\nCalling DeepSeek..."
    )

    context = (
        build_context(
            search_results
        )
    )

    system_prompt = """
You are RepoMind, an AI assistant that helps users
understand open-source software projects.

Answer the user's question using only the retrieved
repository context.

Rules:

1. Use only the provided repository context.
2. Do not invent functions, files, classes, APIs,
   configuration values, or program behavior.
3. If the retrieved context is insufficient,
   clearly say so.
4. Cite sources using [Source 1], [Source 2], etc.
5. When discussing code, mention relevant files.
6. Explain important implementation details clearly.
7. Prefer grounded technical explanations over
   general programming knowledge.
"""

    user_prompt = f"""
Retrieved Repository Context:

{context}


Question:

{question}
"""

    client = (
        get_deepseek_client()
    )

    response = (
        client
        .chat
        .completions
        .create(

            model=
                DEEPSEEK_MODEL,

            messages=[

                {
                    "role":
                        "system",

                    "content":
                        system_prompt
                },

                {
                    "role":
                        "user",

                    "content":
                        user_prompt
                }
            ],

            stream=False
        )
    )

    return (
        response
        .choices[0]
        .message
        .content
    )


# ============================================================
# Complete RAG
# ============================================================

def rag(
    question,
    top_k=5,
    min_similarity=0.0
):
    """
    Complete RepoMind pipeline:

    Vector
        +
    BM25
        ↓
    RRF
        ↓
    Python Code Reranker
        ↓
    Dedup
        ↓
    DeepSeek
    """

    search_results = (
        hybrid_search(

            query=
                question,

            top_k=
                top_k
        )
    )

    if not search_results:

        return (

            "No relevant repository "
            "content was found.",

            search_results
        )

    # --------------------------------------------------------
    # Legacy Vector Similarity Gate
    #
    # Keep threshold=0 during Hybrid/Reranker Evaluation.
    # --------------------------------------------------------

    if min_similarity > 0:

        vector_similarities = [

            result["similarity"]

            for result
            in search_results

            if result.get(
                "similarity"
            ) is not None
        ]

        if vector_similarities:

            best_similarity = max(
                vector_similarities
            )

            if (
                best_similarity
                <
                min_similarity
            ):

                answer = (
                    "The retrieved repository "
                    "content did not pass the "
                    "configured vector similarity "
                    "threshold.\n\n"
                    f"Best vector similarity: "
                    f"{best_similarity:.4f}"
                )

                return (
                    answer,
                    search_results
                )

    answer = (
        generate_answer(

            question=
                question,

            search_results=
                search_results
        )
    )

    return (
        answer,
        search_results
    )


# ============================================================
# Retrieval Debug
# ============================================================

def print_retrieval_results(
    search_results
):

    print(
        "\n"
        + "=" * 70
    )

    print(
        "HYBRID "
        "RETRIEVAL DEBUG"
    )

    print(
        "=" * 70
    )

    for i, result in enumerate(
        search_results,
        start=1
    ):

        metadata = (
            result["metadata"]
        )

        print(
            f"\nResult #{i}"
        )

        print(
            f"File: "
            f"{metadata['path']}"
        )

        print(
            f"Lines: "
            f"{metadata['start_line']}"
            f"-"
            f"{metadata['end_line']}"
        )

        # ----------------------------------------------------
        # Vector
        # ----------------------------------------------------

        print(
            f"Vector Rank: "
            f"{result.get('vector_rank')}"
        )

        similarity = (
            result.get(
                "similarity"
            )
        )

        if similarity is not None:

            print(
                f"Vector Similarity: "
                f"{similarity:.4f}"
            )

        else:

            print(
                "Vector Similarity: N/A"
            )

        # ----------------------------------------------------
        # BM25
        # ----------------------------------------------------

        print(
            f"BM25 Rank: "
            f"{result.get('bm25_rank')}"
        )

        bm25_score = (
            result.get(
                "bm25_score"
            )
        )

        if bm25_score is not None:

            print(
                f"BM25 Score: "
                f"{bm25_score:.4f}"
            )

        else:

            print(
                "BM25 Score: N/A"
            )

        # ----------------------------------------------------
        # RRF
        # ----------------------------------------------------

        print(
            f"RRF Rank: "
            f"{result.get('rrf_rank')}"
        )

        print(
            f"RRF Score: "
            f"{result['rrf_score']:.6f}"
        )

        # ----------------------------------------------------
        # AST metadata
        # ----------------------------------------------------

        print(
            f"Strategy: "
            f"{metadata.get('chunk_strategy', 'N/A')}"
        )

        print(
            f"Type: "
            f"{metadata.get('symbol_type', 'N/A')}"
        )

        print(
            f"Symbol: "
            f"{metadata.get('qualified_name', 'N/A')}"
        )

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        print(
            "\nContent:"
        )

        print(
            result[
                "document"
            ][:700]
        )

        if (
            len(
                result[
                    "document"
                ]
            )
            > 700
        ):

            print("...")

        print(
            "-" * 70
        )


# ============================================================
# CLI
# ============================================================

def main():

    configure_console_encoding()

    parser = argparse.ArgumentParser(

        description=(
            "RepoMind - Hybrid RAG "
            "Hybrid RAG Repository Assistant"
        )
    )

    subparsers = (
        parser.add_subparsers(

            dest="command",

            required=True
        )
    )

    # ========================================================
    # index
    # ========================================================

    index_parser = (
        subparsers.add_parser(

            "index",

            help=(
                "Index a local repository"
            )
        )
    )

    index_parser.add_argument(

        "repo_path",

        help=(
            "Path to local repository"
        )
    )

    index_parser.add_argument(

        "--chunk-size",

        type=int,

        default=1200
    )

    index_parser.add_argument(

        "--chunk-overlap",

        type=int,

        default=200
    )

    index_parser.add_argument(

        "--chunk-strategy",

        choices=["fixed", "ast"],

        default="fixed"
    )

    # ========================================================
    # ask
    # ========================================================

    ask_parser = (
        subparsers.add_parser(

            "ask",

            help=(
                "Ask a question about "
                "the indexed repository"
            )
        )
    )

    ask_parser.add_argument(
        "question"
    )

    ask_parser.add_argument(

        "--top-k",

        type=int,

        default=
            DEFAULT_TOP_K
    )

    ask_parser.add_argument(

        "--threshold",

        type=float,

        default=0.0,

        help=(
            "Legacy vector similarity gate. "
            "Use 0 during Hybrid evaluation."
        )
    )

    # ========================================================
    # Execute
    # ========================================================

    args = (
        parser.parse_args()
    )

    if args.command == "index":

        index_repository(

            repo_path=
                args.repo_path,

            chunk_size=
                args.chunk_size,

            chunk_overlap=
                args.chunk_overlap,

            chunk_strategy=
                args.chunk_strategy
        )

    elif args.command == "ask":

        (
            answer,
            search_results

        ) = rag(

            question=
                args.question,

            top_k=
                args.top_k,

            min_similarity=
                args.threshold
        )

        print_retrieval_results(
            search_results
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "RAG ANSWER"
        )

        print(
            "=" * 70
        )

        print(
            answer
        )


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    main()