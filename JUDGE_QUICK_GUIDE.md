# VeriBrand — 60-second judge guide

No account, password, API key, database or setup is needed.

1. Open the deployed VeriBrand link.
2. Select **Combined demo — multiple issues** and click **Load selected example**.
3. Click **Analyse content**.
4. Expand the findings and inspect the **Claim Passport**.
5. Try the individual examples to see each evidence state:
   - Supported: 7-stage filtration.
   - Contradicted: 9-stage filtration vs approved 7-stage source.
   - Outdated: 2-year warranty whose source expired on 31 Dec 2025.
   - Unverified: 100% harmful-chemical removal with no matching approved source.
6. Select **Needs changes** or **Approved**, enter a reviewer label and save.
7. Open **Review history** to see the decision for this browser session.

## What to look for

The key differentiator is the Claim Passport: evidence status plus the source name, source owner and validity date. VeriBrand is not only a grammar checker. It checks brand rules and factual claims against a configured knowledge base.

## Important scope note

The current judge build uses deterministic Python rules and lexical matching. It does not call a live AI model. Review history is session-only. The knowledge base is fictional and read-only.
