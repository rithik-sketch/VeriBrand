# Deployment checklist — no-configuration judge build

## GitHub
- [ ] Create a public repository named `VeriBrand`.
- [ ] Upload the contents of this folder (not the parent folder).
- [ ] Confirm `app.py`, `requirements.txt`, `brand_rules.json` and `knowledge_base.json` are at repository root.
- [ ] Confirm `.venv`, secrets, passwords and private documents are not uploaded.

## Streamlit Community Cloud
- [ ] Create a new app from the GitHub repository.
- [ ] Select branch `main` and main file path `app.py`.
- [ ] No Streamlit secrets are required for this judge build.
- [ ] Deploy and wait for the app to start.

## Test as a judge
- [ ] Open the public URL in an incognito/private browser.
- [ ] Confirm the app opens without login or configuration.
- [ ] Test each built-in example.
- [ ] Upload TXT, PDF and DOCX samples separately.
- [ ] Confirm evidence statuses, source details and corrections appear.
- [ ] Save a human decision and confirm it appears in Review history.
- [ ] Confirm the shared knowledge base is read-only.

## Known limitations
- Review history is session-only; it is not a durable audit log.
- The app uses deterministic rules and lexical matching, not a live AI model.
- PDF support requires selectable text; scanned-PDF OCR is not included.
- This is a fictional-data hackathon demo, not a production compliance service.
