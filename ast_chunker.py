import ast
import hashlib


# ============================================================
# Chunk ID
# ============================================================

def create_ast_chunk_id(
    file_path,
    chunk_strategy,
    qualified_name,
    start_line,
    end_line,
):
    """
    Create a stable unique ID for every chunk.

    Example raw ID:

    model.py:ast_symbol:GPT.generate:292:313
    """

    raw_id = (
        f"{file_path}:"
        f"{chunk_strategy}:"
        f"{qualified_name}:"
        f"{start_line}:"
        f"{end_line}"
    )

    return hashlib.sha1(
        raw_id.encode("utf-8")
    ).hexdigest()


# ============================================================
# AST Line Helpers
# ============================================================

def get_node_start_line(node):
    """
    Return the first source line belonging to an AST node.

    Decorators are included.

    Example:

    @classmethod
    def from_pretrained(...):

    The start line should point to @classmethod,
    not the def line.
    """

    start_line = getattr(
        node,
        "lineno",
        1
    )

    decorators = getattr(
        node,
        "decorator_list",
        []
    )

    if decorators:

        decorator_lines = [
            decorator.lineno
            for decorator in decorators
            if hasattr(
                decorator,
                "lineno"
            )
        ]

        if decorator_lines:

            start_line = min(
                start_line,
                min(decorator_lines)
            )

    return start_line


def get_node_end_line(node):
    """
    Return the final source line belonging to
    an AST node.

    Python 3.8+ normally provides end_lineno.
    """

    end_line = getattr(
        node,
        "end_lineno",
        None
    )

    if end_line is not None:
        return end_line

    # Fallback for unusual environments
    max_line = getattr(
        node,
        "lineno",
        1
    )

    for child in ast.walk(node):

        child_line = getattr(
            child,
            "lineno",
            None
        )

        if child_line is not None:

            max_line = max(
                max_line,
                child_line
            )

    return max_line


# ============================================================
# Metadata
# ============================================================

def build_metadata(
    base_metadata,
    start_line,
    end_line,
    chunk_strategy,
    symbol_type="",
    symbol_name="",
    qualified_name="",
):
    """
    Build Chroma-compatible metadata.

    Keep metadata values simple:
    strings / ints / floats / bools.
    """

    return {
        "path":
            base_metadata.get(
                "path",
                ""
            ),

        "extension":
            base_metadata.get(
                "extension",
                ""
            ),

        "language":
            base_metadata.get(
                "language",
                ""
            ),

        "start_line":
            int(start_line),

        "end_line":
            int(end_line),

        "chunk_strategy":
            chunk_strategy,

        "symbol_type":
            symbol_type,

        "symbol_name":
            symbol_name,

        "qualified_name":
            qualified_name,
    }


# ============================================================
# Index Text
# ============================================================

def build_index_text(
    content,
    metadata
):
    """
    Text used for Embedding.

    Important:
    This is NOT necessarily the text shown to DeepSeek.

    We enrich embedding input with structural information:

    File: model.py
    Symbol: GPT.generate
    Type: method

    def generate(...):
        ...

    This gives Vector Search additional code-structure signals.
    """

    path = metadata.get(
        "path",
        ""
    )

    qualified_name = metadata.get(
        "qualified_name",
        ""
    )

    symbol_type = metadata.get(
        "symbol_type",
        ""
    )

    header_parts = [
        f"File: {path}"
    ]

    if qualified_name:

        header_parts.append(
            f"Symbol: {qualified_name}"
        )

    if symbol_type:

        header_parts.append(
            f"Type: {symbol_type}"
        )

    header = "\n".join(
        header_parts
    )

    return (
        f"{header}\n\n"
        f"{content}"
    )


# ============================================================
# Fixed Line-range Splitter
# ============================================================

def split_line_range(
    lines,
    start_line,
    end_line,
    base_metadata,
    chunk_size=1200,
    chunk_overlap=200,
    chunk_strategy="ast_residual",
    symbol_type="module",
    symbol_name="",
    qualified_name="",
):
    """
    Split a specific 1-indexed line range.

    Used for:

    - large AST symbols
    - module-level residual code
    - class residual/context code
    - Markdown files
    - AST parse fallback

    The splitter respects complete source lines.
    """

    if not lines:
        return []

    # Clamp requested range
    start_line = max(
        1,
        start_line
    )

    end_line = min(
        len(lines),
        end_line
    )

    if start_line > end_line:
        return []

    chunks = []

    # Convert to 0-based index
    start_index = (
        start_line - 1
    )

    final_index = end_line

    while start_index < final_index:

        end_index = start_index

        current_chars = 0

        # ----------------------------------------------------
        # Determine chunk end
        # ----------------------------------------------------

        while end_index < final_index:

            line_length = (
                len(lines[end_index])
                + 1
            )

            # Do not create an empty chunk just because
            # the first line itself exceeds chunk_size.
            if (
                end_index > start_index
                and
                current_chars
                + line_length
                > chunk_size
            ):
                break

            current_chars += (
                line_length
            )

            end_index += 1

            if (
                current_chars
                >= chunk_size
            ):
                break

        # Safety fallback
        if end_index <= start_index:

            end_index = (
                start_index + 1
            )

        # ----------------------------------------------------
        # Extract chunk
        # ----------------------------------------------------

        chunk_text = "\n".join(
            lines[
                start_index:end_index
            ]
        ).strip()

        actual_start_line = (
            start_index + 1
        )

        actual_end_line = (
            end_index
        )

        if chunk_text:

            metadata = build_metadata(

                base_metadata=
                    base_metadata,

                start_line=
                    actual_start_line,

                end_line=
                    actual_end_line,

                chunk_strategy=
                    chunk_strategy,

                symbol_type=
                    symbol_type,

                symbol_name=
                    symbol_name,

                qualified_name=
                    qualified_name,
            )

            chunk_id = (
                create_ast_chunk_id(

                    file_path=
                        metadata["path"],

                    chunk_strategy=
                        chunk_strategy,

                    qualified_name=
                        qualified_name,

                    start_line=
                        actual_start_line,

                    end_line=
                        actual_end_line,
                )
            )

            chunks.append({
                "id":
                    chunk_id,

                "content":
                    chunk_text,

                "index_text":
                    build_index_text(
                        chunk_text,
                        metadata
                    ),

                "metadata":
                    metadata,
            })

        # ----------------------------------------------------
        # End of requested range
        # ----------------------------------------------------

        if end_index >= final_index:
            break

        # ----------------------------------------------------
        # Character-based overlap
        # ----------------------------------------------------

        overlap_chars = 0

        next_start = (
            end_index
        )

        while next_start > start_index:

            previous_line_length = (
                len(
                    lines[
                        next_start - 1
                    ]
                )
                + 1
            )

            if (
                overlap_chars
                + previous_line_length
                > chunk_overlap
            ):
                break

            overlap_chars += (
                previous_line_length
            )

            next_start -= 1

        # Avoid infinite loop when one line is
        # larger than chunk_overlap/chunk_size.
        if next_start <= start_index:

            next_start = (
                end_index
            )

        start_index = (
            next_start
        )

    return chunks


# ============================================================
# Range Helpers
# ============================================================

def merge_ranges(ranges):
    """
    Merge overlapping or adjacent inclusive ranges.

    Example:

    [(10, 20), (18, 30), (40, 45)]

    becomes:

    [(10, 30), (40, 45)]
    """

    if not ranges:
        return []

    sorted_ranges = sorted(
        ranges,
        key=lambda item: item[0]
    )

    merged = [
        list(sorted_ranges[0])
    ]

    for start, end in (
        sorted_ranges[1:]
    ):

        previous = (
            merged[-1]
        )

        if start <= (
            previous[1] + 1
        ):

            previous[1] = max(
                previous[1],
                end
            )

        else:

            merged.append(
                [start, end]
            )

    return [
        (start, end)
        for start, end
        in merged
    ]


def subtract_ranges(
    base_start,
    base_end,
    covered_ranges
):
    """
    Return parts of [base_start, base_end]
    not covered by symbol ranges.

    All ranges are inclusive.
    """

    if base_start > base_end:
        return []

    relevant_ranges = []

    for start, end in (
        covered_ranges
    ):

        if end < base_start:
            continue

        if start > base_end:
            continue

        relevant_ranges.append(
            (
                max(
                    start,
                    base_start
                ),
                min(
                    end,
                    base_end
                )
            )
        )

    merged = merge_ranges(
        relevant_ranges
    )

    residual = []

    cursor = base_start

    for start, end in merged:

        if cursor < start:

            residual.append(
                (
                    cursor,
                    start - 1
                )
            )

        cursor = max(
            cursor,
            end + 1
        )

    if cursor <= base_end:

        residual.append(
            (
                cursor,
                base_end
            )
        )

    return residual


# ============================================================
# Symbol Chunk
# ============================================================

def create_symbol_chunks(
    node,
    lines,
    base_metadata,
    qualified_name,
    symbol_name,
    symbol_type,
    chunk_size,
    chunk_overlap,
):
    """
    Convert one AST symbol into one or more chunks.

    Small symbol:
        one complete AST chunk

    Large symbol:
        split internally, but every resulting chunk
        keeps the same symbol metadata.
    """

    start_line = (
        get_node_start_line(
            node
        )
    )

    end_line = (
        get_node_end_line(
            node
        )
    )

    if (
        start_line < 1
        or
        end_line < start_line
    ):
        return []

    symbol_text = "\n".join(
        lines[
            start_line - 1:
            end_line
        ]
    ).strip()

    if not symbol_text:
        return []

    # --------------------------------------------------------
    # Symbol fits inside one chunk
    # --------------------------------------------------------

    if (
        len(symbol_text)
        <= chunk_size
    ):

        metadata = build_metadata(

            base_metadata=
                base_metadata,

            start_line=
                start_line,

            end_line=
                end_line,

            chunk_strategy=
                "ast_symbol",

            symbol_type=
                symbol_type,

            symbol_name=
                symbol_name,

            qualified_name=
                qualified_name,
        )

        chunk_id = (
            create_ast_chunk_id(

                file_path=
                    metadata["path"],

                chunk_strategy=
                    "ast_symbol",

                qualified_name=
                    qualified_name,

                start_line=
                    start_line,

                end_line=
                    end_line,
            )
        )

        return [{
            "id":
                chunk_id,

            "content":
                symbol_text,

            "index_text":
                build_index_text(
                    symbol_text,
                    metadata
                ),

            "metadata":
                metadata,
        }]

    # --------------------------------------------------------
    # Large symbol: split inside symbol boundary
    # --------------------------------------------------------

    return split_line_range(

        lines=
            lines,

        start_line=
            start_line,

        end_line=
            end_line,

        base_metadata=
            base_metadata,

        chunk_size=
            chunk_size,

        chunk_overlap=
            chunk_overlap,

        chunk_strategy=
            "ast_symbol_split",

        symbol_type=
            symbol_type,

        symbol_name=
            symbol_name,

        qualified_name=
            qualified_name,
    )


# ============================================================
# Class Processing
# ============================================================

def process_class_node(
    node,
    lines,
    base_metadata,
    parent_qualified_name="",
    chunk_size=1200,
    chunk_overlap=200,
):
    """
    Process a class without duplicating the entire class
    and all its methods.

    Example:

    class GPT:
        x = ...

        def forward(...):
            ...

        def generate(...):
            ...

    becomes roughly:

    GPT class_context
    GPT.forward method
    GPT.generate method

    Nested classes are handled recursively.
    """

    chunks = []

    class_name = node.name

    if parent_qualified_name:

        class_qualified_name = (
            f"{parent_qualified_name}."
            f"{class_name}"
        )

    else:

        class_qualified_name = (
            class_name
        )

    class_start = (
        get_node_start_line(
            node
        )
    )

    class_end = (
        get_node_end_line(
            node
        )
    )

    # Ranges occupied by methods/nested classes
    child_symbol_ranges = []

    # --------------------------------------------------------
    # Process direct methods / nested classes
    # --------------------------------------------------------

    for child in node.body:

        if isinstance(
            child,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            )
        ):

            child_start = (
                get_node_start_line(
                    child
                )
            )

            child_end = (
                get_node_end_line(
                    child
                )
            )

            child_symbol_ranges.append(
                (
                    child_start,
                    child_end
                )
            )

            if isinstance(
                child,
                ast.AsyncFunctionDef
            ):

                symbol_type = (
                    "async_method"
                )

            else:

                symbol_type = (
                    "method"
                )

            qualified_name = (
                f"{class_qualified_name}."
                f"{child.name}"
            )

            chunks.extend(
                create_symbol_chunks(

                    node=
                        child,

                    lines=
                        lines,

                    base_metadata=
                        base_metadata,

                    qualified_name=
                        qualified_name,

                    symbol_name=
                        child.name,

                    symbol_type=
                        symbol_type,

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )

        elif isinstance(
            child,
            ast.ClassDef
        ):

            child_start = (
                get_node_start_line(
                    child
                )
            )

            child_end = (
                get_node_end_line(
                    child
                )
            )

            child_symbol_ranges.append(
                (
                    child_start,
                    child_end
                )
            )

            chunks.extend(
                process_class_node(

                    node=
                        child,

                    lines=
                        lines,

                    base_metadata=
                        base_metadata,

                    parent_qualified_name=
                        class_qualified_name,

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )

    # --------------------------------------------------------
    # Preserve class-level context
    #
    # This catches:
    #
    # class GPT(nn.Module):
    #     some_class_variable = ...
    #     """docstring"""
    #
    # without duplicating method bodies.
    # --------------------------------------------------------

    residual_ranges = subtract_ranges(

        base_start=
            class_start,

        base_end=
            class_end,

        covered_ranges=
            child_symbol_ranges,
    )

    for start_line, end_line in (
        residual_ranges
    ):

        residual_text = "\n".join(
            lines[
                start_line - 1:
                end_line
            ]
        ).strip()

        # Avoid useless chunks that contain
        # only whitespace.
        if not residual_text:
            continue

        chunks.extend(
            split_line_range(

                lines=
                    lines,

                start_line=
                    start_line,

                end_line=
                    end_line,

                base_metadata=
                    base_metadata,

                chunk_size=
                    chunk_size,

                chunk_overlap=
                    chunk_overlap,

                chunk_strategy=
                    "ast_class_context",

                symbol_type=
                    "class_context",

                symbol_name=
                    class_name,

                qualified_name=
                    class_qualified_name,
            )
        )

    return chunks


# ============================================================
# Python AST Chunking
# ============================================================

def split_python_document_ast(
    document,
    chunk_size=1200,
    chunk_overlap=200,
):
    """
    Split one Python source document using AST.

    Strategy:

    1. Top-level functions:
       -> AST symbol chunks

    2. Classes:
       -> methods as symbol chunks
       -> class residual/context preserved

    3. Module-level code not inside functions/classes:
       -> fixed residual chunks

    4. SyntaxError:
       -> fixed fallback chunking
    """

    content = document[
        "content"
    ]

    base_metadata = document[
        "metadata"
    ].copy()

    lines = content.splitlines()

    if not lines:
        return []

    # --------------------------------------------------------
    # Parse Python AST
    # --------------------------------------------------------

    try:

        tree = ast.parse(
            content
        )

    except SyntaxError as error:

        print(
            f"[AST] Parse failed: "
            f"{base_metadata.get('path', '')}"
        )

        print(
            f"      {error}"
        )

        print(
            "      Falling back to fixed chunking."
        )

        chunks = split_line_range(

            lines=
                lines,

            start_line=
                1,

            end_line=
                len(lines),

            base_metadata=
                base_metadata,

            chunk_size=
                chunk_size,

            chunk_overlap=
                chunk_overlap,

            chunk_strategy=
                "fixed_fallback",

            symbol_type=
                "module",

            symbol_name=
                "",

            qualified_name=
                "",
        )

        return assign_chunk_indices(
            chunks
        )

    chunks = []

    # Entire top-level function/class ranges.
    # These will be removed from module-level residual code.
    top_level_symbol_ranges = []

    # --------------------------------------------------------
    # Process top-level AST symbols
    # --------------------------------------------------------

    for node in tree.body:

        # ----------------------------------------------------
        # Top-level Function
        # ----------------------------------------------------

        if isinstance(
            node,
            ast.FunctionDef
        ):

            start_line = (
                get_node_start_line(
                    node
                )
            )

            end_line = (
                get_node_end_line(
                    node
                )
            )

            top_level_symbol_ranges.append(
                (
                    start_line,
                    end_line
                )
            )

            chunks.extend(
                create_symbol_chunks(

                    node=
                        node,

                    lines=
                        lines,

                    base_metadata=
                        base_metadata,

                    qualified_name=
                        node.name,

                    symbol_name=
                        node.name,

                    symbol_type=
                        "function",

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )

        # ----------------------------------------------------
        # Top-level Async Function
        # ----------------------------------------------------

        elif isinstance(
            node,
            ast.AsyncFunctionDef
        ):

            start_line = (
                get_node_start_line(
                    node
                )
            )

            end_line = (
                get_node_end_line(
                    node
                )
            )

            top_level_symbol_ranges.append(
                (
                    start_line,
                    end_line
                )
            )

            chunks.extend(
                create_symbol_chunks(

                    node=
                        node,

                    lines=
                        lines,

                    base_metadata=
                        base_metadata,

                    qualified_name=
                        node.name,

                    symbol_name=
                        node.name,

                    symbol_type=
                        "async_function",

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )

        # ----------------------------------------------------
        # Top-level Class
        # ----------------------------------------------------

        elif isinstance(
            node,
            ast.ClassDef
        ):

            start_line = (
                get_node_start_line(
                    node
                )
            )

            end_line = (
                get_node_end_line(
                    node
                )
            )

            top_level_symbol_ranges.append(
                (
                    start_line,
                    end_line
                )
            )

            chunks.extend(
                process_class_node(

                    node=
                        node,

                    lines=
                        lines,

                    base_metadata=
                        base_metadata,

                    parent_qualified_name=
                        "",

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )

    # --------------------------------------------------------
    # Module-level residual code
    #
    # CRITICAL:
    #
    # nanoGPT train.py contains important executable
    # training logic directly at module level.
    #
    # We MUST NOT discard it just because it is not
    # inside a function.
    # --------------------------------------------------------

    residual_ranges = subtract_ranges(

        base_start=
            1,

        base_end=
            len(lines),

        covered_ranges=
            top_level_symbol_ranges,
    )

    for start_line, end_line in (
        residual_ranges
    ):

        residual_text = "\n".join(
            lines[
                start_line - 1:
                end_line
            ]
        ).strip()

        if not residual_text:
            continue

        chunks.extend(
            split_line_range(

                lines=
                    lines,

                start_line=
                    start_line,

                end_line=
                    end_line,

                base_metadata=
                    base_metadata,

                chunk_size=
                    chunk_size,

                chunk_overlap=
                    chunk_overlap,

                chunk_strategy=
                    "ast_residual",

                symbol_type=
                    "module",

                symbol_name=
                    "",

                qualified_name=
                    "",
            )
        )

    return assign_chunk_indices(
        chunks
    )


# ============================================================
# Markdown / Generic Chunking
# ============================================================

def split_non_python_document(
    document,
    chunk_size=1200,
    chunk_overlap=200,
):
    """
    Markdown currently keeps the fixed-size strategy.

    We are deliberately changing ONLY Python chunking
    in the AST experiment.
    """

    content = document[
        "content"
    ]

    metadata = document[
        "metadata"
    ].copy()

    lines = content.splitlines()

    if not lines:
        return []

    extension = metadata.get(
        "extension",
        ""
    )

    if extension == ".md":

        strategy = (
            "fixed_markdown"
        )

        symbol_type = (
            "document"
        )

    else:

        strategy = (
            "fixed_generic"
        )

        symbol_type = (
            "document"
        )

    chunks = split_line_range(

        lines=
            lines,

        start_line=
            1,

        end_line=
            len(lines),

        base_metadata=
            metadata,

        chunk_size=
            chunk_size,

        chunk_overlap=
            chunk_overlap,

        chunk_strategy=
            strategy,

        symbol_type=
            symbol_type,

        symbol_name=
            "",

        qualified_name=
            "",
    )

    return assign_chunk_indices(
        chunks
    )


# ============================================================
# Chunk Index
# ============================================================

def assign_chunk_indices(
    chunks
):
    """
    Sort chunks by source location and assign a
    deterministic chunk_index.

    Chroma metadata supports integer values.
    """

    chunks.sort(

        key=lambda chunk: (

            chunk[
                "metadata"
            ].get(
                "start_line",
                0
            ),

            chunk[
                "metadata"
            ].get(
                "end_line",
                0
            ),

            chunk[
                "metadata"
            ].get(
                "qualified_name",
                ""
            ),

            chunk[
                "metadata"
            ].get(
                "chunk_strategy",
                ""
            ),
        )
    )

    for index, chunk in enumerate(
        chunks
    ):

        chunk[
            "metadata"
        ][
            "chunk_index"
        ] = index

    return chunks


# ============================================================
# One Document
# ============================================================

def split_document_ast(
    document,
    chunk_size=1200,
    chunk_overlap=200,
):
    """
    Route a document to the appropriate strategy.

    .py:
        AST-aware

    .md:
        fixed-size baseline
    """

    extension = (
        document[
            "metadata"
        ]
        .get(
            "extension",
            ""
        )
        .lower()
    )

    if extension == ".py":

        return (
            split_python_document_ast(

                document=
                    document,

                chunk_size=
                    chunk_size,

                chunk_overlap=
                    chunk_overlap,
            )
        )

    return split_non_python_document(

        document=
            document,

        chunk_size=
            chunk_size,

        chunk_overlap=
            chunk_overlap,
    )


# ============================================================
# All Documents
# ============================================================

def split_documents_ast(
    documents,
    chunk_size=1200,
    chunk_overlap=200,
):
    """
    Main public API.

    Usage from repo_rag.py:

        from ast_chunker import split_documents_ast

        chunks = split_documents_ast(
            documents,
            chunk_size=1200,
            chunk_overlap=200
        )
    """

    all_chunks = []

    python_files = 0

    other_files = 0

    ast_symbol_chunks = 0

    ast_residual_chunks = 0

    class_context_chunks = 0

    fixed_chunks = 0

    for document in documents:

        extension = (
            document[
                "metadata"
            ]
            .get(
                "extension",
                ""
            )
            .lower()
        )

        if extension == ".py":

            python_files += 1

        else:

            other_files += 1

        chunks = split_document_ast(

            document=
                document,

            chunk_size=
                chunk_size,

            chunk_overlap=
                chunk_overlap,
        )

        for chunk in chunks:

            strategy = (
                chunk[
                    "metadata"
                ].get(
                    "chunk_strategy",
                    ""
                )
            )

            if strategy in {
                "ast_symbol",
                "ast_symbol_split",
            }:

                ast_symbol_chunks += 1

            elif strategy == (
                "ast_residual"
            ):

                ast_residual_chunks += 1

            elif strategy == (
                "ast_class_context"
            ):

                class_context_chunks += 1

            else:

                fixed_chunks += 1

        all_chunks.extend(
            chunks
        )

    # --------------------------------------------------------
    # Global chunk index
    # --------------------------------------------------------

    for index, chunk in enumerate(
        all_chunks
    ):

        chunk[
            "metadata"
        ][
            "global_chunk_index"
        ] = index

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 70
    )

    print(
        "AST CHUNKING STATISTICS"
    )

    print(
        "=" * 70
    )

    print(
        f"Python files: "
        f"{python_files}"
    )

    print(
        f"Other files: "
        f"{other_files}"
    )

    print(
        f"AST symbol chunks: "
        f"{ast_symbol_chunks}"
    )

    print(
        f"AST residual chunks: "
        f"{ast_residual_chunks}"
    )

    print(
        f"Class context chunks: "
        f"{class_context_chunks}"
    )

    print(
        f"Fixed / Markdown chunks: "
        f"{fixed_chunks}"
    )

    print(
        f"Total chunks: "
        f"{len(all_chunks)}"
    )

    return all_chunks


# ============================================================
# Debug Helper
# ============================================================

def print_ast_chunks(
    chunks,
    limit=None,
):
    """
    Optional debug helper.

    Useful before rebuilding the Chroma index.

    Example:

        print_ast_chunks(chunks, limit=20)
    """

    if limit is None:

        selected_chunks = (
            chunks
        )

    else:

        selected_chunks = (
            chunks[:limit]
        )

    print(
        "\n"
        + "=" * 70
    )

    print(
        "AST CHUNK DEBUG"
    )

    print(
        "=" * 70
    )

    for index, chunk in enumerate(
        selected_chunks,
        start=1
    ):

        metadata = (
            chunk["metadata"]
        )

        print(
            f"\nChunk #{index}"
        )

        print(
            f"File: "
            f"{metadata.get('path', '')}"
        )

        print(
            f"Strategy: "
            f"{metadata.get('chunk_strategy', '')}"
        )

        print(
            f"Type: "
            f"{metadata.get('symbol_type', '')}"
        )

        print(
            f"Symbol: "
            f"{metadata.get('qualified_name', '')}"
        )

        print(
            f"Lines: "
            f"{metadata.get('start_line', '')}"
            f"-"
            f"{metadata.get('end_line', '')}"
        )

        print(
            "\nContent:"
        )

        print(
            chunk[
                "content"
            ][:800]
        )

        if (
            len(
                chunk[
                    "content"
                ]
            )
            > 800
        ):

            print("...")

        print(
            "-" * 70
        )