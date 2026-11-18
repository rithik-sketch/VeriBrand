# VeriBrand — Proof Before Publish

VeriBrand is a no-login, no-API-key Streamlit judge demo for pre-publication brand governance. It checks content against fictional brand rules and approved facts, shows source evidence and suggested corrections, and lets the reviewer make the final decision.

## Judge experience

1. Open the deployed application link. No account, API key or database setup is required.
2. In **Review content**, choose a built-in example or upload a TXT, selectable-text PDF or DOCX.
3. Click **Analyse content**.
4. Open each finding. Inspect the rule, reason, suggested correction and Claim Passport (status, source, owner and validity date).
5. Choose **Approved** or **Needs changes**, enter a reviewer label and save.
6. Open **Review history** to see the decision for the current browser session.

## What makes VeriBrand different

Ordinary grammar tools mainly correct language. VeriBrand focuses on brand governance and claim substantiation: it compares factual statements with approved source records and reports **Supported, Contradicted, Outdated or Unverified**. It does not treat a missing source as proof that a claim is false. A human reviewer makes the final decision.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Open `http://localhost:8501`.

## Technical implementation

- Python + Streamlit interface.
- Configured JSON brand rules and approved-fact knowledge base.
- Regular-expression checks and conservative lexical token-overlap matching with attribute groups.
- TXT, selectable-text PDF (`pypdf`) and DOCX (`python-docx`) text extraction.
- Session-only human review history in judge mode.

## Honest scope and limitations

- **PDF support:** Upload PDFs containing selectable text. Scanned, image-only and embedded-image PDFs require OCR, which is not included.
- **Review history:** Temporary session history for the current browser/app session only. It is not permanent storage and may clear when the session ends or the app restarts.
- **Claim checking:** VeriBrand uses a conservative rules-based baseline with local JSON facts and lexical matching. It is not an AI fact-checker and does not establish legal or scientific truth.
- **Human review:** The tool recommends findings and evidence states; the human reviewer makes the final approval or rejection decision.
- The current deployed demo does **not** call a live AI model. The app's checks are deterministic Python rules and lexical matching.
- ChatGPT may have been used as a development assistant; see `AI_USAGE_DISCLOSURE.md` and update it to match the tools actually used by the team.
- No login or role management is included in this judge build. The shared knowledge base is read-only.
- Review history is session-only and may clear when the browser session ends.
- Scanned PDFs and embedded image text are not OCR-processed.
- The evidence engine is not legal, scientific or regulatory fact-checking. Always inspect the source and use human review.
- Fictional AquaNest demo data only. Do not upload confidential or personal information.

## Tests

Run: `py -m unittest discover -s tests -v`

See `ROUND2_TEST_REPORT.md` for the included regression and document-upload tests.

## Deployment

Upload the contents of this folder to a GitHub repository with `app.py` and `requirements.txt` at the root. Deploy using Streamlit Community Cloud with `app.py` as the entry point. No secrets are needed for the judge demo. Test the deployed URL in an incognito browser and upload all three sample documents.
