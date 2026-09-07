---
pretty_name: PatentMatch Temporal and Component-Clean Extension
language:
- en
license: cc-by-4.0
task_categories:
- text-classification
tags:
- patents
- prior-art
- temporal-split
- text-pair-classification
- reranking
- benchmark
size_categories:
- 10K<n<100K
---

# PatentMatch Temporal and Component-Clean Extension

## Status

Private research preview. Patent text files have not yet been uploaded.

## Source

This benchmark is derived from **PatentMatch: A Dataset for Matching Patent
Claims with Prior Art**.

- Paper: https://arxiv.org/abs/2012.13919
- Official project: https://hpi.de/naumann/s/patentmatch
- Source repository: https://github.com/julian-risch/PatentMatch

## License

The PatentMatch paper states that the dataset is released under the
**Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

Users must cite the original PatentMatch work and preserve attribution.

## Label semantics

- `1`: **X citation** — a passage considered novelty-prejudicial or highly
  relevant to the novelty/inventive-step assessment.
- `0`: **A citation** — a passage representing technological background or
  the general state of the art.

These labels represent different degrees of examiner-assessed relevance.
They should not be described as arbitrary positive and random-negative pairs.

## Primary task

Binary claim–prior-art passage classification.

Input:

    claim + prior-art passage

Output:

    X citation or A citation

## Auxiliary task

Pairwise discrimination within groups sharing identical claim text.

This is an auxiliary evaluation, not a full-corpus first-stage retrieval task.
Most exact-claim groups contain approximately one X passage and one A passage.

## Clean split

| Split | Pair rows |
|---|---:|
| Train | 16,928 |
| Development | 3,652 |
| Test | 3,650 |
| Quarantine | 1,046 |

The retained dataset contains 24,230 pairs. Application identities, cited
documents, claim texts, and passage texts do not overlap across the
train/development/test splits.

The splits are temporally ordered by application filing date.

## Temporal ranges

- Train: 2012-07-04 to 2016-09-21
- Development: 2016-09-28 to 2017-05-10
- Test: 2017-05-17 to 2018-01-31

## Multi-date exact-text groups

There are 71 exact-claim-text groups containing rows
from multiple filing dates.

- They remain valid for the primary row-level classification task.
- They remain in overall exact-text pairwise analysis.
- They are excluded from year-specific pairwise analysis.

## Current automatic baselines

The following automatic baselines have been evaluated:

- TF-IDF cosine similarity
- BM25
- zero-shot MiniLM bi-encoder
- zero-shot PatentSBERTa
- train-supervised MS MARCO MiniLM cross-encoder

The current results show that lexical, zero-shot dense, patent-domain dense,
and train-supervised cross-encoder baselines remain close to random under the
temporal and component-clean split.

Primary metrics:

- Accuracy
- Macro-F1
- ROC-AUC
- Average Precision

Auxiliary metrics:

- Pairwise Accuracy
- MRR
- nDCG

Because most auxiliary groups contain only two candidates, MRR and nDCG
should always be interpreted together with their random baselines.

## Human annotation extension

A 100-pair double-blind claim-element decomposition pilot package has been
generated. Human annotation is not yet complete.

Planned human annotations include:

- claim-element decomposition;
- element-level support labels;
- evidence spans;
- all-elements completeness;
- missing-element identification;
- annotator confidence.

## Limitations

1. This is currently a text-pair classification benchmark, not a full-corpus
   first-stage retrieval benchmark.
2. The auxiliary pairwise task is constructed from identical claim-text
   groups rather than a guaranteed shared application-level query ID.
3. Family metadata is not currently available.
4. Human claim-element and evidence-span annotations are pending.
5. An A citation should not be interpreted as universally irrelevant in all
   legal or technical contexts.

## Citation

Users should cite the original PatentMatch paper:

Risch, Julian, Nicolas Alder, Christoph Hewel, and Ralf Krestel.
"PatentMatch: A Dataset for Matching Patent Claims with Prior Art."
2021.
