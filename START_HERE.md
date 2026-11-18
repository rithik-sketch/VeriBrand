# Start here — judge demo

## If you are a judge

1. Open the public VeriBrand link.
2. No sign-in, password, API key, database or setup is required.
3. Choose a built-in example or upload one of the files in `sample_uploads`.
4. Click **Analyse content**.
5. Inspect findings and the Claim Passport.
6. Record **Approved** or **Needs changes** and check Review history.

## If you are running it locally (Windows)

Open this folder in VS Code → Terminal → New Terminal, then run one line at a time:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

Open `http://localhost:8501`.

## Before submission

- Fill team name, college, team ID and member roles in the report PDF.
- Add only verified GitHub and deployed application URLs.
- Deploy the app and test it in an incognito browser.
- Upload `test_post.txt`, `test_ad.pdf` and `test_email.docx` one by one.
- Do not claim live AI, login or managed database features. They are not part of this simplified judge build.
