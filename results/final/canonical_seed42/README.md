# Canonical MiniLM-CE Seed-42 Results

This directory contains aggregate results for the canonical
MiniLM-CE seed-42 run on the XART-temporal test split.

## Verified alignment

- Test pairs: 3,650
- Ranking-eligible queries: 1,815
- Canonical-to-manifest alignment: `_row_id`
- Analysis-to-canonical alignment:
  `query_key + label + passage_length`
- Count-mismatch groups: 0
- Duplicate alignment rows: 0

## Seed-42 results

| Metric | Value |
|---|---:|
| Accuracy | 0.5112 |
| Macro-F1 | 0.5101 |
| ROC-AUC | 0.5266 |
| Average precision | 0.5279 |
| Pairwise accuracy | 0.5331 |

These values describe one canonical seed-42 run. The main
benchmark table reports the independent three-seed mean.

Because this repository is public, the pair-level aligned
Parquet artifact is retained locally and is not published.
