"""File loading. Knows nothing about Streamlit."""

import io
from pathlib import Path

import pandas as pd


def load_file(source, filename=None):
    """Read a CSV or Excel file into a DataFrame.

    Args:
        source:   a path string, Path, or file-like buffer
        filename: original name, needed when `source` is a buffer

    Returns:
        pandas.DataFrame

    Raises:
        ValueError: if the file type isn't supported or can't be parsed
    """
    name = filename or str(source)
    ext = Path(name).suffix.lower()

    if ext == ".csv":
        return _read_csv(source)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(source)

    raise ValueError(f"Unsupported file type: '{ext}'. Upload a CSV or Excel file.")


def _read_csv(source):
    """Read a CSV, falling back through common encodings."""
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(source, encoding=encoding)
        except UnicodeDecodeError:
            _rewind(source)
        except pd.errors.ParserError as e:
            raise ValueError(f"This doesn't look like a valid CSV. ({e})")

    raise ValueError("Couldn't decode this file — try re-saving it as UTF-8.")


def _rewind(source):
    """Reset a buffer's cursor so it can be read again."""
    if hasattr(source, "seek"):
        source.seek(0)