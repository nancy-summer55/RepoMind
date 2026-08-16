import os
from pathlib import Path


# Files we currently support
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".md": "markdown",
}


# Directories that should not be indexed
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


# Skip very large files for now
MAX_FILE_SIZE = 512 * 1024  # 512 KB


def load_repository(repo_path):
    """
    Read all supported files from a local repository.

    Returns:
        [
            {
                "content": "...",
                "metadata": {
                    "path": "src/auth.py",
                    "extension": ".py",
                    "language": "python"
                }
            }
        ]
    """

    root = Path(repo_path).expanduser().resolve()

    if not root.exists():
        raise ValueError(
            f"Repository does not exist: {root}"
        )

    if not root.is_dir():
        raise ValueError(
            f"Repository path is not a directory: {root}"
        )

    documents = []

    for current_dir, dir_names, file_names in os.walk(root):

        # Prevent os.walk from entering ignored directories
        dir_names[:] = [
            name
            for name in dir_names
            if name not in IGNORED_DIRS
        ]

        current_path = Path(current_dir)

        for file_name in file_names:

            file_path = current_path / file_name

            extension = file_path.suffix.lower()

            # Only read .py and .md for now
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            # Ignore large files
            try:
                file_size = file_path.stat().st_size
            except OSError:
                continue

            if file_size > MAX_FILE_SIZE:
                print(
                    f"Skip large file: {file_path}"
                )
                continue

            # Read text
            try:
                content = file_path.read_text(
                    encoding="utf-8",
                    errors="replace"
                )
            except OSError:
                print(
                    f"Failed to read: {file_path}"
                )
                continue

            # Ignore empty files
            if not content.strip():
                continue

            relative_path = file_path.relative_to(root)

            document = {
                "content": content,

                "metadata": {
                    "path": relative_path.as_posix(),
                    "extension": extension,
                    "language": SUPPORTED_EXTENSIONS[
                        extension
                    ]
                }
            }

            documents.append(document)

    return documents