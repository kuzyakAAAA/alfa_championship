"""Safe CSV loading for paths and Streamlit uploads."""

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from utils.validators import validate_required_columns


def load_csv_file(source: str | Path | BinaryIO) -> pd.DataFrame:
    """Load a UTF-8/UTF-8-SIG CSV and validate its basic shape."""

    name = str(getattr(source, "name", source))
    if not name.lower().endswith(".csv"):
        raise ValueError("Поддерживаются только файлы CSV")

    if hasattr(source, "read"):
        raw = source.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
    else:
        raw = Path(source).read_bytes()

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            frame = pd.read_csv(BytesIO(raw), encoding=encoding)
            frame.columns = [str(column).strip().lower() for column in frame.columns]
            validate_required_columns(frame.columns)
            return frame
        except UnicodeDecodeError as error:
            last_error = error
    raise ValueError("Файл должен быть сохранен в UTF-8 или UTF-8-SIG") from last_error
