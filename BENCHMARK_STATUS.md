# Benchmark Status

## Current frozen dataset

- Retained pair rows: 24,230
- Train rows: 16,928
- Development rows: 3,652
- Test rows: 3,650
- Quarantine rows: 1,046
- Exact-claim-text groups: 12,026
- Multi-date exact-text groups: 71

## Correct task framing

### Primary task

Temporal and component-clean X-vs-A claim–passage classification.

### Auxiliary task

Exact-claim-text pairwise discrimination.

The project does not currently claim to provide a full-corpus first-stage
patent retrieval benchmark.

## Automatic baseline status

Completed baselines:

- TF-IDF
- BM25
- zero-shot MiniLM
- zero-shot PatentSBERTa
- train-supervised MS MARCO MiniLM cross-encoder

Best development pairwise method:

    MSMARCO_MINILM_CROSS_ENCODER

Best numerical test pairwise method:

    TFIDF

Best numerical test ROC-AUC method:

    MINILM_ZERO_SHOT

## Interpretation

The tested automatic baselines remain close to random on the temporal test
split.

This motivates claim-element and evidence-span annotation, but it does not
by itself prove that temporal distribution shift is the only cause.

No material train-to-test shift was detected in the previously audited
surface features, such as length and lexical overlap.

## Remaining work

1. Complete two-annotator claim-element decomposition.
2. Align independently produced elements.
3. Measure inter-annotator agreement.
4. Annotate evidence spans and all-elements completeness.
5. Perform human-centered failure analysis on hard examples.
6. Add family metadata if a reliable public mapping becomes available.
7. Freeze and publish benchmark version 1.0 with complete attribution.
