# ingest.py
import pandas as pd
from pathlib import Path

def load_file(source, filename=None):
    """Read a CSV or Excel file. Works with a path or an uploaded buffer."""
    name = filename or str(source)
    ext = Path(name).suffix.lower()

    if ext == ".csv":
        return pd.read_csv(source)
    elif ext in (".xlsx", ".xls"):
        return pd.read_excel(source)
    raise ValueError(f"Unsupported file type: {ext}")