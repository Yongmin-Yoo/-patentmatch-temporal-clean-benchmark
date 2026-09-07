# Data Release Policy

## Current policy

The repository is private during development.

Patent claims, prior-art passages, and derived train/dev/test CSV files are
not uploaded until the redistribution conditions for the underlying
PatentMatch/EPO-derived text are verified.

## Files that may be stored now

- Aggregate reports
- JSON manifests
- Evaluation specifications
- Code
- Non-text statistics

## Files that must not be publicly uploaded yet

- Full claim text
- Full prior-art passage text
- Raw PatentMatch archives
- Derived CSV files containing the original text
- Human annotation workbooks containing claim text

## Required checks before release

1. Verify upstream dataset redistribution terms.
2. Add attribution and citation.
3. Select an accurate dataset license.
4. Remove accidental personal or secret information.
5. Freeze a versioned data manifest.
