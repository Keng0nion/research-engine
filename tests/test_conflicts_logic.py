"""Unit test for conflict detection logic (no DB, synthetic rows)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.conflicts import detect_numeric_conflicts, detect_polarity_conflicts

rows = [
    {"id": "E-1", "claim": "Deep learning improves protein structure accuracy significantly",
     "numbers_json": '[{"metric": "accuracy", "value": 0.92, "unit": "gdt_ts"}]'},
    {"id": "E-2", "claim": "Deep learning does not improve protein folding in low-data regimes",
     "numbers_json": '[{"metric": "accuracy", "value": 0.41, "unit": "gdt_ts"}]'},
    {"id": "E-3", "claim": "无关陈述", "numbers_json": None},
]

num = detect_numeric_conflicts(rows)
assert len(num) == 1, num
assert num[0]["kind"] == "numbers" and num[0]["topic"] == "accuracy"
assert set(num[0]["evidence_ids"]) == {"E-1", "E-2"}

pol = detect_polarity_conflicts(rows)
assert len(pol) >= 1, pol
assert set(pol[0]["evidence_ids"]) == {"E-1", "E-2"}

# same-value numbers must NOT conflict
rows2 = [
    {"id": "A", "claim": "x", "numbers_json": '[{"metric": "m", "value": 1.0}]'},
    {"id": "B", "claim": "y", "numbers_json": '[{"metric": "m", "value": 1.02}]'},
]
assert detect_numeric_conflicts(rows2) == []

print("CONFLICT-LOGIC-OK numeric=1 polarity>=1")
