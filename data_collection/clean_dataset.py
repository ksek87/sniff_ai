"""
One-time script: strip scraper artifacts from dataset.csv Notes column.

The scraper appended '. Discover more details!' to the last note in every
row — e.g. "['Rose', 'Cedar. Discover more details!']". This removes it.

Run from the repo root:
    python data_collection/clean_dataset.py
"""
import csv
import re
import sys
from pathlib import Path

_CSV = Path(__file__).parent / "dataset.csv"
_ARTIFACT = re.compile(r"\.?\s*Discover more details!", re.IGNORECASE)


def clean_notes(raw: str) -> str:
    return _ARTIFACT.sub("", raw).strip()


def main() -> None:
    rows = []
    with _CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row["Notes"] = clean_notes(row["Notes"])
            rows.append(row)

    with _CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Cleaned {len(rows)} rows → {_CSV}")


if __name__ == "__main__":
    main()
