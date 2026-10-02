"""Asset lookup for the supplied UNO card artwork."""
from __future__ import annotations

from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parent.parent / "cards" / "PineTools.com_files"
_CARD_FILES: dict[tuple[str | None, str], Path] = {}

for _color, _row in (("red", 1), ("yellow", 2), ("green", 3), ("blue", 4)):
    _folder = ASSET_ROOT / _color
    for _value, _column in zip(map(str, range(1, 9)), range(2, 10)):
        _CARD_FILES[(_color, _value)] = _folder / f"row-{_row}-column-{_column}.png"
    _CARD_FILES[(_color, "stop")] = _folder / f"row-{_row}-column-11.png"
    _CARD_FILES[(_color, "+2")] = _folder / f"row-{_row}-column-13.png"

_wild_files = sorted(
    (ASSET_ROOT / "wild").glob("*.png"),
    key=lambda path: tuple(int(part) for part in path.stem.replace("row-", "").replace("column-", "").split("-")),
)
for _index, _path in enumerate(_wild_files):
    _CARD_FILES[(None, "wild" if _index < 4 else "+4")] = _path


def card_image_path(color: str | None, value: str) -> Path | None:
    """Return the PNG representing a card, if the supplied asset exists."""
    path = _CARD_FILES.get((color, str(value)))
    return path if path is not None and path.is_file() else None


def card_image_url(color: str | None, value: str) -> str | None:
    """Return the URL used by the web client for a card image."""
    path = card_image_path(color, value)
    return f"/cards/{path.relative_to(ASSET_ROOT).as_posix()}" if path else None
