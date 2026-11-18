# VeriBrand Round 2 — validation report

## Test scope

This report covers the source-level claim matching and document extraction tests included in this package. It does not claim that a public deployment or a browser session has been independently tested.

## Claim-status regression tests

| Test | Expected status |
|---|---|
| 7-stage filtration matches approved specification | Supported |
| 9-stage filtration differs from approved 7-stage specification | Contradicted |
| 5-litre capacity matches approved fact | Supported |
| 2-year warranty refers to an expired source | Outdated |
| Founded in 2020 differs from approved 2018 fact | Contradicted |
| 100% harmful-chemical removal has no matching approved source | Unverified |

## Document upload tests

| File | Expected observation |
|---|---|
| `test_post.txt` | Extract text; flag incorrect product naming and guarantee wording |
| `test_ad.pdf` | Extract selectable text; mark 9-stage claim Contradicted |
| `test_email.docx` | Extract text; flag 100% purity wording and mark unsupported claim Unverified |

## Judge-mode behaviour

- No login, API key, database or secrets are required.
- Judges can use built-in examples or upload supported documents.
- The shared knowledge base is read-only.
- Human decisions are saved in browser session state only.
- No content is automatically published.

## Limitations

The rule engine is a conservative lexical MVP baseline, not legal/scientific fact-checking. PDF extraction requires selectable text; OCR is not included. The current app does not call a live AI model. Public hosting, cross-device behaviour and browser UI still need a real deployment smoke test by the team.


Automated test command result in build environment: **9/9 tests passed** (6 claim-status regression tests + 3 document-upload tests).
