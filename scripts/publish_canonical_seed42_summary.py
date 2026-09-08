from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile

import pandas as pd
import requests


# =========================================================
# 설정
# =========================================================
GITHUB_OWNER = "Yongmin-Yoo"
GITHUB_REPO = "-patentmatch-temporal-clean-benchmark"

REPOSITORY_URL = (
    f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
)

SOURCE_ROOT = Path(
    "/content/drive/MyDrive/"
    "PatentSearchBench/external/PatentMatch"
)

SOURCE_DIR = (
    SOURCE_ROOT / "benchmark_resolution_analysis"
)

METRICS_SOURCE = (
    SOURCE_DIR / "canonical_seed42_point_metrics.csv"
)

PARQUET_SOURCE = (
    SOURCE_DIR
    / "aligned_baseline_predictions_canonical_seed42.parquet"
)

DESTINATION_DIR = Path(
    "results/final/canonical_seed42"
)

REPOSITORY_SCRIPT_PATH = Path(
    "scripts/publish_canonical_seed42_summary.py"
)


# =========================================================
# 보조 함수
# =========================================================
def run(command, cwd=None, env=None, check=True):
    result = subprocess.run(
        [str(value) for value in command],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )

    token = os.environ.get("GITHUB_TOKEN", "")

    stdout = (result.stdout or "").replace(
        token,
        "[REDACTED]",
    )
    stderr = (result.stderr or "").replace(
        token,
        "[REDACTED]",
    )

    if stdout.strip():
        print(stdout.strip())

    if result.returncode != 0 and stderr.strip():
        print(stderr.strip())

    if check and result.returncode != 0:
        raise RuntimeError(
            "명령 실행 실패: "
            + " ".join(str(value) for value in command)
        )

    return result


def sha256_file(path, chunk_size=1024 * 1024):
    digest = hashlib.sha256()

    with path.open("rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


# =========================================================
# 1. Token과 원본 파일 확인
# =========================================================
token = os.environ.get(
    "GITHUB_TOKEN",
    "",
).strip()

assert token, (
    "환경변수 GITHUB_TOKEN을 불러오지 못했습니다."
)

assert METRICS_SOURCE.exists(), (
    f"집계 결과 파일이 없습니다: {METRICS_SOURCE}"
)

assert PARQUET_SOURCE.exists(), (
    f"검증용 parquet이 없습니다: {PARQUET_SOURCE}"
)


# =========================================================
# 2. 로컬 검증
# 공개 GitHub에는 parquet을 올리지 않음
# =========================================================
metrics = pd.read_csv(METRICS_SOURCE)
aligned = pd.read_parquet(PARQUET_SOURCE)

assert len(metrics) == 1, (
    "metrics CSV는 한 행이어야 합니다."
)

assert len(aligned) == 3650, (
    f"예상 행 수가 아닙니다: {len(aligned)}"
)

required_metrics = {
    "accuracy": 0.511233,
    "macro_f1": 0.510094,
    "roc_auc": 0.526635,
    "average_precision": 0.527879,
    "pairwise_accuracy": 0.533104,
}

for metric, expected in required_metrics.items():
    assert metric in metrics.columns, (
        f"metrics CSV에 {metric} 열이 없습니다."
    )

    actual = float(metrics.iloc[0][metric])

    assert abs(actual - expected) <= 0.00001, (
        f"{metric} 불일치: "
        f"actual={actual}, expected≈{expected}"
    )

print("=== LOCAL VERIFICATION ===")
print("Rows:", len(aligned))
print(metrics.to_string(index=False))
print("Public upload excludes pair-level parquet.")


# =========================================================
# 3. GitHub 저장소 확인
# =========================================================
api_url = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}"
)

response = requests.get(
    api_url,
    headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    timeout=30,
)

assert response.status_code == 200, (
    f"GitHub API 오류: HTTP {response.status_code}\n"
    f"{response.text[:500]}"
)

repository_info = response.json()

assert repository_info.get("private") is False, (
    "현재 코드는 public repository 전용입니다."
)

default_branch = repository_info.get(
    "default_branch",
    "main",
)

print("\n=== REPOSITORY ===")
print("Repository:", repository_info["full_name"])
print("Visibility:", repository_info["visibility"])
print("Branch:", default_branch)


# =========================================================
# 4. 안전한 Git 인증 준비
# =========================================================
temporary_root = Path(
    tempfile.mkdtemp(
        prefix="canonical_seed42_public_"
    )
)

clone_directory = temporary_root / "repository"
askpass_path = temporary_root / "git_askpass.sh"

askpass_path.write_text(
    """#!/bin/sh
case "$1" in
    *Username*) echo "x-access-token" ;;
    *Password*) echo "$GITHUB_TOKEN" ;;
    *) echo "" ;;
esac
""",
    encoding="utf-8",
)

askpass_path.chmod(
    askpass_path.stat().st_mode | stat.S_IXUSR
)

git_environment = os.environ.copy()
git_environment["GITHUB_TOKEN"] = token
git_environment["GIT_ASKPASS"] = str(
    askpass_path
)
git_environment["GIT_ASKPASS_REQUIRE"] = "force"
git_environment["GIT_TERMINAL_PROMPT"] = "0"


try:
    # =====================================================
    # 5. 저장소 clone
    # =====================================================
    run(
        [
            "git",
            "clone",
            "--branch",
            default_branch,
            "--single-branch",
            REPOSITORY_URL + ".git",
            clone_directory,
        ],
        env=git_environment,
    )

    destination = (
        clone_directory / DESTINATION_DIR
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =====================================================
    # 6. 집계 CSV만 복사
    # =====================================================
    metrics_destination = (
        destination / METRICS_SOURCE.name
    )

    shutil.copy2(
        METRICS_SOURCE,
        metrics_destination,
    )

    # =====================================================
    # 7. 검증 metadata 생성
    # =====================================================
    metric_values = {}

    for key, value in metrics.iloc[0].to_dict().items():
        if hasattr(value, "item"):
            value = value.item()

        metric_values[key] = value

    metadata = {
        "artifact": (
            "Canonical MiniLM-CE seed-42 "
            "XART-temporal aggregate results"
        ),
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "repository": REPOSITORY_URL,
        "publication_scope": (
            "Aggregate metrics only; "
            "pair-level parquet retained locally"
        ),
        "seed": 42,
        "test_rows": 3650,
        "ranking_queries": 1815,
        "alignment_verification": {
            "canonical_to_manifest":
                "_row_id",
            "aligned_to_canonical": [
                "query_key",
                "label",
                "passage_length",
            ],
            "count_mismatch_groups": 0,
            "aligned_duplicate_rows": 0,
            "canonical_duplicate_rows": 0,
            "status": "one-to-one verified",
        },
        "metrics_unrounded": metric_values,
        "paper_values_rounded": {
            "accuracy": 0.5112,
            "macro_f1": 0.5101,
            "roc_auc": 0.5266,
            "average_precision": 0.5279,
            "pairwise_accuracy": 0.5331,
        },
        "published_file": {
            "name": metrics_destination.name,
            "size_bytes":
                metrics_destination.stat().st_size,
            "sha256": sha256_file(
                metrics_destination
            ),
        },
        "excluded_private_artifact": {
            "name": PARQUET_SOURCE.name,
            "rows": 3650,
            "sha256": sha256_file(
                PARQUET_SOURCE
            ),
            "reason": (
                "Pair-level artifact is not released "
                "through the public repository"
            ),
        },
    }

    metadata_path = (
        destination
        / "canonical_seed42_metadata.json"
    )

    metadata_path.write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # =====================================================
    # 8. README 작성
    # =====================================================
    readme_path = destination / "README.md"

    readme_path.write_text(
        """# Canonical MiniLM-CE Seed-42 Results

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
""",
        encoding="utf-8",
    )

    # =====================================================
    # 9. 실행 스크립트도 .py로 저장
    # =====================================================
    repository_script = (
        clone_directory / REPOSITORY_SCRIPT_PATH
    )

    repository_script.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copy2(
        Path(__file__),
        repository_script,
    )

    # =====================================================
    # 10. Git 설정
    # =====================================================
    run(
        [
            "git",
            "config",
            "user.name",
            "Yongmin Yoo",
        ],
        cwd=clone_directory,
        env=git_environment,
    )

    run(
        [
            "git",
            "config",
            "user.email",
            "yongminyoo91@users.noreply.github.com",
        ],
        cwd=clone_directory,
        env=git_environment,
    )

    # =====================================================
    # 11. 공개 가능한 파일만 stage
    # =====================================================
    files_to_commit = [
        metrics_destination.relative_to(
            clone_directory
        ),
        metadata_path.relative_to(
            clone_directory
        ),
        readme_path.relative_to(
            clone_directory
        ),
        repository_script.relative_to(
            clone_directory
        ),
    ]

    run(
        [
            "git",
            "add",
            "--",
            *[
                str(path)
                for path in files_to_commit
            ],
        ],
        cwd=clone_directory,
        env=git_environment,
    )

    staged_files = run(
        [
            "git",
            "diff",
            "--cached",
            "--name-only",
        ],
        cwd=clone_directory,
        env=git_environment,
    ).stdout.strip()

    print("\n=== STAGED FILES ===")
    print(
        staged_files
        if staged_files
        else "No changes"
    )

    # pair-level parquet이 staged되지 않았는지 확인
    assert (
        "aligned_baseline_predictions"
        not in staged_files
    ), (
        "Pair-level parquet이 stage되었습니다. "
        "업로드를 중단합니다."
    )

    # =====================================================
    # 12. Commit 및 push
    # =====================================================
    if staged_files:
        run(
            [
                "git",
                "commit",
                "-m",
                (
                    "Add canonical seed-42 "
                    "aggregate evaluation results"
                ),
            ],
            cwd=clone_directory,
            env=git_environment,
        )

        run(
            [
                "git",
                "push",
                "origin",
                default_branch,
            ],
            cwd=clone_directory,
            env=git_environment,
        )
    else:
        print(
            "동일한 결과가 이미 저장되어 있습니다."
        )

    commit_hash = run(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        cwd=clone_directory,
        env=git_environment,
    ).stdout.strip()

    print("\n=== COMPLETE ===")
    print("Commit:", commit_hash)
    print(
        "URL:",
        f"{REPOSITORY_URL}/tree/"
        f"{default_branch}/{DESTINATION_DIR}",
    )

finally:
    token = None
    git_environment.pop("GITHUB_TOKEN", None)

    if temporary_root.exists():
        shutil.rmtree(
            temporary_root,
            ignore_errors=True,
        )
