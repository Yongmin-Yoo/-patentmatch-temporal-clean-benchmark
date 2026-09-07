#!/usr/bin/env python3
"""Audit structural overlap between the official PatentMatch split and XART.

The script compares the official PatentMatch ultra-balanced train/test split
with the XART component-clean temporal split. It reports only aggregate
statistics and does not export patent claim or passage text.

Example:
    python audit_official_patentmatch_split.py \
        --official-train patentmatch_train_ultrabalanced.tsv \
        --official-test patentmatch_test_ultrabalanced.tsv \
        --xart-train train.csv \
        --xart-dev dev.csv \
        --xart-test test.csv \
        --xart-quarantine quarantine.csv \
        --output-dir results/audit
"""

from pathlib import Path
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import re
import unicodedata

import numpy as np
import pandas as pd


REQUIRED_OFFICIAL_COLUMNS = {
    "claim_id",
    "patent_application_id",
    "cited_document_id",
    "text",
    "text_b",
    "label",
    "date",
}

REQUIRED_XART_COLUMNS = {
    "claim_id",
    "patent_application_id",
    "cited_document_id",
    "text",
    "text_b",
    "label",
    "date",
    "_source_split",
    "_row_id",
    "_supercomponent_id",
    "_benchmark_split",
}


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()

    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def normalize_text(value):
    if pd.isna(value):
        return ""

    value = unicodedata.normalize("NFKC", str(value))
    value = re.sub(r"\s+", " ", value).strip()
    return value


def hash_text(prefix, value):
    normalized = normalize_text(value)

    return hashlib.sha256(
        f"{prefix}\u241f{normalized}".encode("utf-8")
    ).hexdigest()


def validate_columns(frame, required, name):
    missing = sorted(required - set(frame.columns))

    if missing:
        raise ValueError(
            f"{name} is missing required columns: {missing}"
        )


def audit_cross_split_identity(
    frame,
    key_column,
    identity_name,
):
    train = frame[
        frame["_source_split"] == "original_train"
    ].copy()

    test = frame[
        frame["_source_split"] == "original_test"
    ].copy()

    train_values = set(
        train[key_column].dropna().astype(str)
    )

    test_values = set(
        test[key_column].dropna().astype(str)
    )

    shared_values = train_values & test_values

    train_affected = train[
        train[key_column].astype(str).isin(shared_values)
    ]

    test_affected = test[
        test[key_column].astype(str).isin(shared_values)
    ]

    return {
        "identity_type": identity_name,
        "train_unique": len(train_values),
        "test_unique": len(test_values),
        "shared_unique": len(shared_values),
        "shared_rate_test": (
            len(shared_values) / len(test_values)
            if test_values
            else np.nan
        ),
        "affected_train_rows": len(train_affected),
        "affected_test_rows": len(test_affected),
        "affected_test_row_rate": (
            len(test_affected) / len(test)
            if len(test) > 0
            else np.nan
        ),
        "affected_test_claim_ids": int(
            test_affected["claim_id"].nunique()
        ),
        "affected_test_exact_queries": int(
            test_affected["_claim_text_key"].nunique()
        ),
    }


def crossing_group_summary(
    frame,
    group_column,
    group_name,
):
    group_table = (
        frame.groupby(group_column)
        .agg(
            split_count=(
                "_source_split",
                "nunique",
            ),
            rows=(
                "_row_id",
                "size",
            ),
            train_rows=(
                "_source_split",
                lambda values: (
                    values == "original_train"
                ).sum(),
            ),
            test_rows=(
                "_source_split",
                lambda values: (
                    values == "original_test"
                ).sum(),
            ),
            exact_queries=(
                "_claim_text_key",
                "nunique",
            ),
            applications=(
                "patent_application_id",
                "nunique",
            ),
            cited_documents=(
                "cited_document_id",
                "nunique",
            ),
            min_date=(
                "_audit_date",
                "min",
            ),
            max_date=(
                "_audit_date",
                "max",
            ),
        )
        .reset_index()
    )

    crossing = group_table[
        group_table["split_count"] > 1
    ].copy()

    crossing_ids = set(
        crossing[group_column]
    )

    affected = frame[
        frame[group_column].isin(crossing_ids)
    ].copy()

    affected_test = affected[
        affected["_source_split"] == "original_test"
    ].copy()

    original_test_rows = int(
        (
            frame["_source_split"]
            == "original_test"
        ).sum()
    )

    summary = {
        "group_type": group_name,
        "total_groups": int(len(group_table)),
        "cross_split_groups": int(len(crossing)),
        "cross_split_group_rate": (
            len(crossing) / len(group_table)
            if len(group_table) > 0
            else np.nan
        ),
        "affected_rows": int(len(affected)),
        "affected_train_rows": int(
            (
                affected["_source_split"]
                == "original_train"
            ).sum()
        ),
        "affected_test_rows": int(len(affected_test)),
        "affected_test_row_rate": (
            len(affected_test) / original_test_rows
            if original_test_rows > 0
            else np.nan
        ),
        "affected_test_claim_ids": int(
            affected_test["claim_id"].nunique()
        ),
        "affected_test_exact_queries": int(
            affected_test["_claim_text_key"].nunique()
        ),
    }

    return summary


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Audit the official PatentMatch split against "
            "the XART component-clean temporal split."
        )
    )

    parser.add_argument(
        "--official-train",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--official-test",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--xart-train",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--xart-dev",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--xart-test",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--xart-quarantine",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
    )

    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    official_train = pd.read_csv(
        args.official_train,
        sep="\t",
        low_memory=False,
    )

    official_test = pd.read_csv(
        args.official_test,
        sep="\t",
        low_memory=False,
    )

    xart_frames = []

    for split_name, path in [
        ("train", args.xart_train),
        ("dev", args.xart_dev),
        ("test", args.xart_test),
        ("quarantine", args.xart_quarantine),
    ]:
        frame = pd.read_csv(
            path,
            low_memory=False,
        )

        validate_columns(
            frame,
            REQUIRED_XART_COLUMNS,
            f"XART {split_name}",
        )

        observed_splits = set(
            frame["_benchmark_split"]
            .dropna()
            .astype(str)
        )

        if observed_splits != {split_name}:
            raise ValueError(
                f"Unexpected benchmark split values in "
                f"{path}: {observed_splits}"
            )

        xart_frames.append(frame)

    validate_columns(
        official_train,
        REQUIRED_OFFICIAL_COLUMNS,
        "Official training set",
    )

    validate_columns(
        official_test,
        REQUIRED_OFFICIAL_COLUMNS,
        "Official test set",
    )

    full_xart = pd.concat(
        xart_frames,
        ignore_index=True,
    )

    if full_xart["_row_id"].duplicated().any():
        raise ValueError(
            "The combined XART files contain duplicate row IDs."
        )

    allowed_source_splits = {
        "original_train",
        "original_test",
    }

    observed_source_splits = set(
        full_xart["_source_split"]
        .dropna()
        .astype(str)
    )

    if observed_source_splits != allowed_source_splits:
        raise ValueError(
            "Unexpected source split values: "
            f"{observed_source_splits}"
        )

    if full_xart["_supercomponent_id"].isna().any():
        raise ValueError(
            "Missing structural supercomponent IDs."
        )

    full_xart["_claim_text_key"] = (
        full_xart["text"].map(
            lambda value: hash_text("claim", value)
        )
    )

    full_xart["_passage_text_key"] = (
        full_xart["text_b"].map(
            lambda value: hash_text("passage", value)
        )
    )

    full_xart["_audit_date"] = pd.to_datetime(
        full_xart["date"].astype(str),
        format="%Y%m%d",
        errors="coerce",
    )

    identity_columns = [
        ("claim_id", "Claim ID"),
        (
            "patent_application_id",
            "Patent application",
        ),
        (
            "cited_document_id",
            "Cited document",
        ),
        (
            "_claim_text_key",
            "Exact claim text",
        ),
        (
            "_passage_text_key",
            "Exact passage text",
        ),
        (
            "_supercomponent_id",
            "Structural supercomponent",
        ),
    ]

    identity_audit = pd.DataFrame(
        [
            audit_cross_split_identity(
                full_xart,
                column,
                name,
            )
            for column, name in identity_columns
        ]
    )

    component_summary = crossing_group_summary(
        full_xart,
        "_supercomponent_id",
        "Structural supercomponent",
    )

    query_summary = crossing_group_summary(
        full_xart,
        "_claim_text_key",
        "Exact claim text",
    )

    crossing_summary = pd.DataFrame(
        [
            component_summary,
            query_summary,
        ]
    )

    raw_counts = pd.Series(
        {
            "original_train": len(official_train),
            "original_test": len(official_test),
        },
        name="raw_rows",
    )

    clean_counts = (
        full_xart["_source_split"]
        .value_counts()
        .rename("clean_rows")
    )

    cleaning_summary = pd.concat(
        [
            raw_counts,
            clean_counts,
        ],
        axis=1,
    ).fillna(0)

    cleaning_summary["removed_rows"] = (
        cleaning_summary["raw_rows"]
        - cleaning_summary["clean_rows"]
    )

    cleaning_summary["retention_rate"] = (
        cleaning_summary["clean_rows"]
        / cleaning_summary["raw_rows"]
    )

    cleaning_summary.loc["total"] = {
        "raw_rows": cleaning_summary["raw_rows"].sum(),
        "clean_rows": cleaning_summary["clean_rows"].sum(),
        "removed_rows": (
            cleaning_summary["removed_rows"].sum()
        ),
        "retention_rate": (
            cleaning_summary["clean_rows"].sum()
            / cleaning_summary["raw_rows"].sum()
        ),
    }

    transition_matrix = pd.crosstab(
        full_xart["_source_split"],
        full_xart["_benchmark_split"],
        margins=True,
    )

    official_clean_test_ids = set(
        full_xart.loc[
            full_xart["_source_split"]
            == "original_test",
            "_row_id",
        ]
    )

    xart_test_ids = set(
        full_xart.loc[
            full_xart["_benchmark_split"]
            == "test",
            "_row_id",
        ]
    )

    shared_test_ids = (
        official_clean_test_ids & xart_test_ids
    )

    test_overlap = pd.DataFrame(
        [
            {
                "official_raw_test_rows": len(
                    official_test
                ),
                "official_clean_test_rows": len(
                    official_clean_test_ids
                ),
                "xart_test_rows": len(
                    xart_test_ids
                ),
                "shared_test_rows": len(
                    shared_test_ids
                ),
                "official_clean_test_covered_by_xart": (
                    len(shared_test_ids)
                    / len(official_clean_test_ids)
                ),
                "xart_test_from_official_test": (
                    len(shared_test_ids)
                    / len(xart_test_ids)
                ),
                "official_test_not_in_xart_test": (
                    len(
                        official_clean_test_ids
                        - xart_test_ids
                    )
                ),
                "xart_test_not_from_official_test": (
                    len(
                        xart_test_ids
                        - official_clean_test_ids
                    )
                ),
            }
        ]
    )

    source_date_ranges = (
        full_xart.groupby("_source_split")[
            "_audit_date"
        ]
        .agg(["count", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "_source_split": "split",
            }
        )
    )

    source_date_ranges.insert(
        0,
        "split_definition",
        "PatentMatch official",
    )

    benchmark_date_ranges = (
        full_xart.groupby("_benchmark_split")[
            "_audit_date"
        ]
        .agg(["count", "min", "max"])
        .reset_index()
        .rename(
            columns={
                "_benchmark_split": "split",
            }
        )
    )

    benchmark_date_ranges.insert(
        0,
        "split_definition",
        "XART",
    )

    date_ranges = pd.concat(
        [
            source_date_ranges,
            benchmark_date_ranges,
        ],
        ignore_index=True,
    )

    identity_audit.to_csv(
        args.output_dir
        / "official_identity_overlap_audit.csv",
        index=False,
    )

    crossing_summary.to_csv(
        args.output_dir
        / "official_crossing_summary.csv",
        index=False,
    )

    cleaning_summary.to_csv(
        args.output_dir
        / "official_cleaning_summary.csv",
        index_label="source_split",
    )

    transition_matrix.to_csv(
        args.output_dir
        / "official_to_xart_transition_counts.csv",
        index_label="source_split",
    )

    test_overlap.to_csv(
        args.output_dir
        / "official_vs_xart_test_overlap.csv",
        index=False,
    )

    date_ranges.to_csv(
        args.output_dir
        / "official_and_xart_date_ranges.csv",
        index=False,
    )

    input_hashes = {
        "official_train_sha256": sha256_file(
            args.official_train
        ),
        "official_test_sha256": sha256_file(
            args.official_test
        ),
        "xart_train_sha256": sha256_file(
            args.xart_train
        ),
        "xart_dev_sha256": sha256_file(
            args.xart_dev
        ),
        "xart_test_sha256": sha256_file(
            args.xart_test
        ),
        "xart_quarantine_sha256": sha256_file(
            args.xart_quarantine
        ),
    }

    summary = {
        "status": "OFFICIAL_SPLIT_AUDIT_COMPLETE",
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "official_raw_rows": {
            "train": int(len(official_train)),
            "test": int(len(official_test)),
            "total": int(
                len(official_train)
                + len(official_test)
            ),
        },
        "clean_rows": int(len(full_xart)),
        "removed_during_cleaning": int(
            len(official_train)
            + len(official_test)
            - len(full_xart)
        ),
        "xart_rows": {
            str(key): int(value)
            for key, value in (
                full_xart["_benchmark_split"]
                .value_counts()
                .to_dict()
                .items()
            )
        },
        "official_component_crossing": (
            component_summary
        ),
        "official_exact_query_crossing": (
            query_summary
        ),
        "official_vs_xart_test_overlap": (
            test_overlap.iloc[0].to_dict()
        ),
        "date_ranges": [
            {
                "split_definition": row[
                    "split_definition"
                ],
                "split": row["split"],
                "count": int(row["count"]),
                "min": (
                    row["min"].strftime("%Y-%m-%d")
                    if pd.notna(row["min"])
                    else None
                ),
                "max": (
                    row["max"].strftime("%Y-%m-%d")
                    if pd.notna(row["max"])
                    else None
                ),
            }
            for _, row in date_ranges.iterrows()
        ],
        "input_hashes": input_hashes,
        "release_scope": (
            "Aggregate statistics only. "
            "No patent claim or passage text is exported."
        ),
    }

    with open(
        args.output_dir
        / "official_split_audit_summary.json",
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            summary,
            handle,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    component = component_summary
    overlap = test_overlap.iloc[0]

    report = f"""# Official PatentMatch Split Audit

## Scope

This audit compares the official PatentMatch ultra-balanced train/test split with the XART component-clean temporal split. It uses the structural supercomponents produced by the XART construction pipeline. The released results contain aggregate statistics only and do not include patent claim or passage text.

## Source data

| Item | Rows |
|---|---:|
| Official training split | {len(official_train):,} |
| Official test split | {len(official_test):,} |
| Official total | {len(official_train) + len(official_test):,} |
| Rows retained after cleaning | {len(full_xart):,} |
| Rows removed during cleaning | {len(official_train) + len(official_test) - len(full_xart):,} |

## Structural audit

The official split contains no repeated claim IDs across training and test. However, {component["cross_split_groups"]:,} of {component["total_groups"]:,} structural supercomponents span both partitions. These components contain {component["affected_test_rows"]:,} cleaned official test pairs, corresponding to {component["affected_test_row_rate"]:.2%} of the cleaned official test set, and affect {component["affected_test_exact_queries"]:,} exact-claim queries.

The component definition captures broader dependencies induced by shared patent applications, cited documents, exact claim text, exact passage text, and their transitive connectivity. The audit therefore distinguishes direct claim-ID overlap from broader structural dependence.

## Test-set continuity

The cleaned official test set contains {int(overlap["official_clean_test_rows"]):,} pairs. XART retains {int(overlap["shared_test_rows"]):,} of these pairs in its final test set, corresponding to {overlap["official_clean_test_covered_by_xart"]:.2%} of the cleaned official test set. All XART test pairs originate from the official PatentMatch test partition.

## Interpretation

The official PatentMatch split already prevents direct claim-ID overlap. XART adds a stricter component-level isolation criterion that removes broader structural connections across training, development, and test. The result should be interpreted as an audited split extension rather than as a new collection of patent text.

## Reproduction

Run:

```bash
python scripts/audit_official_patentmatch_split.py \\
  --official-train /path/to/patentmatch_train_ultrabalanced.tsv \\
  --official-test /path/to/patentmatch_test_ultrabalanced.tsv \\
  --xart-train /path/to/xart/train.csv \\
  --xart-dev /path/to/xart/dev.csv \\
  --xart-test /path/to/xart/test.csv \\
  --xart-quarantine /path/to/xart/quarantine.csv \\
  --output-dir results/audit
```

The script requires an authorized local copy of PatentMatch and the locally
reconstructed XART split. Patent text is not redistributed.
"""

    with open(
        args.output_dir
        / "official_split_audit_report.md",
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write(report)

    print("=" * 100)
    print("IDENTITY AUDIT")
    print("=" * 100)
    print(
        identity_audit.to_string(
            index=False,
            float_format=lambda value: f"{value:.6f}",
        )
    )

    print("\n" + "=" * 100)
    print("CROSSING SUMMARY")
    print("=" * 100)
    print(
        crossing_summary.to_string(
            index=False,
            float_format=lambda value: f"{value:.6f}",
        )
    )

    print("\nAudit outputs:")
    print(args.output_dir)


if __name__ == "__main__":
    main()
