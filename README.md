# PatentMatch Temporal-Clean Benchmark Extension

This is a private development repository for a temporal- and
component-clean extension of PatentMatch.

## Current status

- Input pairs before quarantine: 25,276
- Retained clean pairs: 24,230
- Quarantined pairs: 1,046
- Quarantine rate: 4.14%
- Train rows: 16,928
- Development rows: 3,652
- Test rows: 3,650
- Cross-split claim/application/document/text overlap: 0
- Strict temporal ordering: verified
- Unique claim queries: 12,026
- Test ranking-eligible queries: 1,815 / 1,815

## Benchmark framing

The current data primarily supports:

1. Claim–prior-art passage pair classification
2. Pairwise passage ranking
3. Pairwise document ranking
4. Human claim-element and evidence-span annotation

Because most queries contain approximately two candidates, this should not
yet be described as a large-corpus first-stage retrieval benchmark.

## Data release status

Patent text and train/dev/test files are **not included in this repository**.

The upstream PatentMatch code repository uses an MIT license, but the
redistribution terms covering the derived EPO patent text must be verified
separately before publishing the processed dataset.

## Planned baselines

- TF-IDF cosine similarity
- BM25
- Dense bi-encoder
- Cross-encoder
- Pairwise accuracy, Accuracy, Macro-F1, ROC-AUC, MRR, and nDCG

## Human annotation

A 100-pair double-blind claim-element decomposition package has been
generated. Human annotation may be completed later.

## Upstream dataset

PatentMatch: A Dataset for Matching Patent Claims with Prior Art

- Paper: https://arxiv.org/abs/2012.13919
- Repository: https://github.com/julian-risch/PatentMatch
