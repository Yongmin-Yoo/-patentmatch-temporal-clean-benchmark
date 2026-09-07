# Official PatentMatch Split Audit

## Scope

This audit compares the official PatentMatch ultra-balanced train/test split with the XART component-clean temporal split. It uses the structural supercomponents produced by the XART construction pipeline. The released results contain aggregate statistics only and do not include patent claim or passage text.

## Source data

| Item | Rows |
|---|---:|
| Official training split | 20,272 |
| Official test split | 5,068 |
| Official total | 25,340 |
| Rows retained after cleaning | 25,276 |
| Rows removed during cleaning | 64 |

## Structural audit

The official split contains no repeated claim IDs across training and test. However, 20 of 1,486 structural supercomponents span both partitions. These components contain 448 cleaned official test pairs, corresponding to 8.86% of the cleaned official test set, and affect 224 exact-claim queries.

The component definition captures broader dependencies induced by shared patent applications, cited documents, exact claim text, exact passage text, and their transitive connectivity. The audit therefore distinguishes direct claim-ID overlap from broader structural dependence.

## Test-set continuity

The cleaned official test set contains 5,056 pairs. XART retains 3,650 of these pairs in its final test set, corresponding to 72.19% of the cleaned official test set. All XART test pairs originate from the official PatentMatch test partition.

## Interpretation

The official PatentMatch split already prevents direct claim-ID overlap. XART adds a stricter component-level isolation criterion that removes broader structural connections across training, development, and test. The result should be interpreted as an audited split extension rather than as a new collection of patent text.

## Reproduction

Run:

```bash
python scripts/audit_official_patentmatch_split.py \
  --official-train /path/to/patentmatch_train_ultrabalanced.tsv \
  --official-test /path/to/patentmatch_test_ultrabalanced.tsv \
  --xart-train /path/to/xart/train.csv \
  --xart-dev /path/to/xart/dev.csv \
  --xart-test /path/to/xart/test.csv \
  --xart-quarantine /path/to/xart/quarantine.csv \
  --output-dir results/audit
```

The script requires an authorized local copy of PatentMatch and the locally
reconstructed XART split. Patent text is not redistributed.
