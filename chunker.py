import hashlib


def create_chunk_id(
    file_path,
    start_line,
    end_line
):
    """
    Create a stable unique ID for every chunk.
    """

    raw_id = (
        f"{file_path}:"
        f"{start_line}:"
        f"{end_line}"
    )

    return hashlib.sha1(
        raw_id.encode("utf-8")
    ).hexdigest()


def split_document(
    document,
    chunk_size=1200,
    chunk_overlap=200
):
    """
    Split one document into chunks.

    chunk_size:
        Approximate maximum number of characters.

    chunk_overlap:
        Approximate number of characters shared
        between neighboring chunks.
    """

    content = document["content"]

    metadata = document["metadata"]

    lines = content.splitlines()

    if not lines:
        return []

    chunks = []

    start = 0
    chunk_index = 0

    while start < len(lines):

        end = start

        current_chars = 0

        # -----------------------------------------
        # Find where this chunk should end
        # -----------------------------------------

        while end < len(lines):

            line_length = len(lines[end]) + 1

            if (
                end > start
                and current_chars + line_length
                > chunk_size
            ):
                break

            current_chars += line_length

            end += 1

            if current_chars >= chunk_size:
                break

        # -----------------------------------------
        # Build chunk text
        # -----------------------------------------

        chunk_text = "\n".join(
            lines[start:end]
        ).strip()

        start_line = start + 1
        end_line = end

        if chunk_text:

            chunk_id = create_chunk_id(
                metadata["path"],
                start_line,
                end_line
            )

            chunk = {
                "id": chunk_id,

                "content": chunk_text,

                "metadata": {
                    "path": metadata["path"],
                    "extension": metadata[
                        "extension"
                    ],
                    "language": metadata[
                        "language"
                    ],
                    "start_line": start_line,
                    "end_line": end_line,
                    "chunk_index": chunk_index
                }
            }

            chunks.append(chunk)

            chunk_index += 1

        # -----------------------------------------
        # Reached the end of the file
        # -----------------------------------------

        if end >= len(lines):
            break

        # -----------------------------------------
        # Calculate overlap
        # -----------------------------------------

        overlap_chars = 0

        next_start = end

        while next_start > start:

            previous_line_length = (
                len(lines[next_start - 1]) + 1
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

        # Prevent infinite loop
        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def split_documents(
    documents,
    chunk_size=1200,
    chunk_overlap=200
):
    """
    Split all repository documents.
    """

    all_chunks = []

    for document in documents:

        chunks = split_document(
            document=document,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        all_chunks.extend(chunks)

    return all_chunks