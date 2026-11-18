import hashlib, json, re
from pathlib import Path
from datetime import datetime, date
import streamlit as st

BASE = Path(__file__).parent
RULES_FILE = BASE / "brand_rules.json"
FACTS_FILE = BASE / "knowledge_base.json"

st.set_page_config(page_title="VeriBrand", page_icon="🛡️", layout="wide")

def read_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        st.warning(f"Could not read {path.name}; using an empty/default dataset.")
    return default

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


BRAND = read_json(RULES_FILE, {"organisation":"Demo organisation", "prohibited":[], "terminology":[], "product_names":[], "facts":[]})

# Judge mode is intentionally zero-configuration: no API key, login or database required.
def load_facts():
    return read_json(FACTS_FILE, BRAND.get("facts", []))

if not FACTS_FILE.exists():
    initial = []
    for i, fact in enumerate(BRAND.get("facts", []), 1):
        initial.append({"id":i, "claim":fact["claim"], "source":fact.get("source","Not supplied"), "owner":fact.get("owner","Not supplied"), "valid_until":fact.get("valid_until","2099-12-31"), "status":"Approved"})
    write_json(FACTS_FILE, initial)

if "result" not in st.session_state:
    st.session_state.result = None
if "demo_history" not in st.session_state:
    st.session_state.demo_history = []
if "content_input" not in st.session_state:
    st.session_state.content_input = "Meet the Aqua Nest PureFlow! Our BEST purifier guarantees 100% pure water. It includes a 9-stage filtration process and removes 100% of all harmful chemicals!!!"

STOP = {"the","a","an","is","are","was","were","be","been","being","and","or","of","to","in","on","for","with","our","this","that","it","has","have","includes","include","contains","contain","from","by","as","at","its","product","process"}
def tokens(value):
    return {x for x in re.findall(r"[a-z0-9]+", value.lower()) if x not in STOP and len(x) > 1}
def numbers(value):
    return re.findall(r"\d+(?:\.\d+)?", value)

# Attribute groups stop unrelated product facts (e.g. filtration stages vs storage capacity)
# from being treated as comparable evidence.
ATTRIBUTE_GROUPS = {
    "filtration": {"stage", "stages", "filter", "filters", "filtration"},
    "capacity": {"capacity", "storage", "litre", "litres", "liter", "liters"},
    "weight": {"weight", "weighs", "kg", "gram", "grams"},
    "warranty": {"warranty", "guarantee", "years", "year"},
    "founding": {"founded", "established", "founding"},
    "content": {"contains", "content", "mg", "milligram", "milligrams"},
}
def attribute_groups(value):
    words = set(re.findall(r"[a-z0-9]+", value.lower()))
    groups = {name for name, terms in ATTRIBUTE_GROUPS.items() if words & terms}
    # "5-litre" and "5 litre" both map to capacity; "2-year warranty" maps to warranty.
    if re.search(r"\b\d+(?:\.\d+)?\s*(?:l|litre|litres|liter|liters)\b", value, re.I):
        groups.add("capacity")
    if re.search(r"\b\d+\s*[- ]?years?\b", value, re.I) and "warranty" in words:
        groups.add("warranty")
    return groups

def claim_status(sentence, facts):
    """Conservative lexical matching: compare only facts about the same identifiable attribute."""
    s_tokens = tokens(sentence)
    s_groups = attribute_groups(sentence)
    candidates = []
    for fact in facts:
        fact_text = fact.get("claim", "")
        f_tokens = tokens(fact_text)
        if not s_tokens or not f_tokens:
            continue
        f_groups = attribute_groups(fact_text)

        # If either side identifies an attribute, require a shared attribute.
        # This prevents a capacity claim being compared with filtration or warranty facts.
        if (s_groups or f_groups) and not (s_groups & f_groups):
            continue

        overlap = len(s_tokens & f_tokens)
        score = overlap / max(1, len(s_tokens | f_tokens))
        # Require a meaningful lexical connection beyond a shared company/product name.
        shared_meaningful = (s_tokens & f_tokens) - {"aquanest", "pureflow"}
        if not shared_meaningful:
            continue
        candidates.append((score, fact))

    if not candidates:
        return {"status":"Unverified", "fact":None, "score":0,
                "reason":"No approved fact about the same product attribute was found. This does not prove the claim is false."}

    best_score, best = max(candidates, key=lambda item: item[0])
    if best_score < 0.20:
        return {"status":"Unverified", "fact":None, "score":best_score,
                "reason":"No sufficiently close approved fact about the same attribute was found. This does not prove the claim is false."}

    # Check approval and expiry before comparing values. Expired evidence must never
    # be presented as current support or as a current contradiction.
    if best.get("status") != "Approved":
        return {"status":"Unverified", "fact":best, "score":best_score,
                "reason":"The matching record is not marked Approved; human review is required."}
    try:
        expired = date.fromisoformat(best.get("valid_until", "2099-12-31")) < date.today()
    except (ValueError, TypeError):
        expired = True
    if expired:
        return {"status":"Outdated", "fact":best, "score":best_score,
                "reason":"A matching approved fact exists, but its validity date has passed. Obtain a current source before relying on it."}

    s_nums, f_nums = numbers(sentence), numbers(best.get("claim", ""))
    same_attribute = bool(s_groups & attribute_groups(best.get("claim", "")))
    if s_nums and f_nums and s_nums != f_nums and same_attribute:
        return {"status":"Contradicted", "fact":best, "score":best_score,
                "reason":"The claim has a different numeric value from an approved fact about the same attribute. Human verification is required."}
    if best_score >= 0.30:
        return {"status":"Supported", "fact":best, "score":best_score,
                "reason":"A close approved fact about the same attribute was found. Confirm that the wording and context preserve the source meaning."}
    return {"status":"Unverified", "fact":best, "score":best_score,
            "reason":"A possible related fact was found, but the match is not strong enough to mark the claim supported."}

def extract_uploaded_text(upload):
    """Extract selectable text from TXT, PDF or DOCX uploads."""
    name = upload.name.lower()
    raw = upload.getvalue()
    if name.endswith(".txt"):
        try:
            return raw.decode("utf-8-sig"), "TXT"
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace"), "TXT"
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(raw))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()
        if not text:
            raise ValueError("No selectable text was found. This may be a scanned PDF; OCR is not included in this MVP yet.")
        return text, "PDF"
    if name.endswith(".docx"):
        from docx import Document
        import io
        document = Document(io.BytesIO(raw))
        parts = [para.text for para in document.paragraphs if para.text.strip()]
        for table in document.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text.strip() for cell in row.cells))
        text = "\n\n".join(parts).strip()
        if not text:
            raise ValueError("No readable text was found in this DOCX file.")
        return text, "DOCX"
    raise ValueError("Unsupported file type. Upload TXT, PDF or DOCX.")

def analyse(text, facts):
    findings = []
    low = text.lower()
    for rule in BRAND.get("prohibited", []):
        if rule["phrase"].lower() in low:
            findings.append({"type":"Brand rule","severity":"High","rule":rule["rule"],"found":rule["phrase"],"why":rule["why"],"fix":rule["fix"],"evidence":"Brand guideline: prohibited wording"})
    for term in BRAND.get("terminology", []):
        if re.search(r"\b"+re.escape(term["avoid"])+r"\b", text, re.I):
            findings.append({"type":"Terminology","severity":"Medium","rule":f"Use approved term: {term['use']}","found":term["avoid"],"why":term["why"],"fix":f"Use “{term['use']}” instead.","evidence":"Brand guideline: terminology"})
    for p in BRAND.get("product_names", []):
        wrong = p["wrong"]
        # Explicit spacing variants of the configured incorrect name. Keep the
        # canonical approved spelling (e.g. AquaNest PureFlow) unflagged.
        variants = {wrong}
        compact_parts = re.split(r"[\s-]+", wrong.strip())
        if len(compact_parts) >= 3:
            variants.add(" ".join(compact_parts[:2]) + " " + "".join(compact_parts[2:]))
            variants.add("".join(compact_parts[:2]) + " " + " ".join(compact_parts[2:]))
        matched_variant = next((v for v in variants if re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", text, re.I)), None)
        if matched_variant:
            findings.append({"type":"Product naming","severity":"Medium","rule":f"Approved product name is {p['right']}","found":matched_variant,"why":"Product names must match the approved brand terminology, including exact spelling and spacing.","fix":f"Use “{p['right']}”.","evidence":"Approved product-name list"})
    high_risk_patterns = [
        (r"\bcure\s+(?:anxiety|depression|stress|disease|illness)\b", "Medical cure claim"),
        (r"\bclinically\s+proven\b", "Clinical-evidence claim"),
        (r"\b100\s*%\s*doctor[- ]approved\b", "Absolute medical endorsement claim"),
        (r"\bside[- ]effect[- ]free\b", "Absolute safety claim"),
        (r"\b(?:only thing|only solution)\s+you need\b", "Exclusive treatment/solution claim"),
    ]
    for pattern, label in high_risk_patterns:
        for match in re.finditer(pattern, text, re.I):
            findings.append({"type":"High-risk claim","severity":"High","rule":"Health, clinical, endorsement and absolute-safety claims require approved, current evidence.","found":match.group(0),"why":f"This wording is a high-risk {label.lower()}. It requires specialist evidence review; this flag does not establish truth or falsity.","fix":"Remove the claim or provide a current, approved source reviewed by the appropriate subject-matter/compliance owner.","evidence":"Human evidence review required"})
    cues = ["%", "million", "billion", "founded", "certified", "number one", "no. 1", "first", "fastest", "guarantee", "proven", "removes", "contains", "includes", "stage", "mg", "years"]
    seen = set()
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        s = sentence.strip()
        if not s:
            continue
        matched = claim_status(s, facts)
        is_claim = (any(c in s.lower() for c in cues if c not in ("guarantee",)) or matched["fact"] is not None)
        if not is_claim:
            continue
        key = re.sub(r"\W+", "", s.lower())
        if key in seen:
            continue
        seen.add(key)
        status = matched["status"]
        severity = "High" if status in ("Contradicted", "Outdated") else "Medium" if status == "Unverified" else "Low"
        fact = matched["fact"]
        evidence = "No matching approved source — Unverified"
        why = matched["reason"]
        if fact:
            evidence = f"{status} · {fact.get('source','Source not supplied')} · Owner: {fact.get('owner','Not supplied')} · Valid until: {fact.get('valid_until','Not supplied')}"
        findings.append({"type":"Factual claim","severity":severity,"rule":"Important factual claims must be supported by a current approved source.","found":s,"why":why,"fix":"Check the cited source and wording with the source owner; revise or remove the claim if it cannot be substantiated.","evidence":evidence,"claim_status":status,"source_fact":fact})
    if text.count("!") >= 3:
        findings.append({"type":"Tone","severity":"Low","rule":"Avoid excessive exclamation marks.","found":f"{text.count('!')} exclamation marks","why":"The approved voice is calm and confident.","fix":"Keep at most one exclamation mark and use a specific benefit-led sentence.","evidence":"Brand guideline: tone"})
    superlatives = list(re.finditer(r"\b(?:BEST|WORLD|NUMBER ONE|NO\.\s*1)\b", text, re.I))
    for match in superlatives:
        findings.append({"type":"Brand rule","severity":"Medium","rule":"Avoid unsubstantiated superlative or market-leadership claims.","found":match.group(0),"why":"Superlatives such as best or number one need specific, current evidence and approval.","fix":"Remove the superlative or provide an approved source that substantiates the comparison.","evidence":"Brand guideline: substantiation required"})
    if re.search(r"\b(AMAZING|BEST|BUY NOW)\b", text):
        findings.append({"type":"Tone","severity":"Medium","rule":"Avoid shouting-style promotional language.","found":"Uppercase promotional wording","why":"The brand avoids exaggerated, pressure-based wording.","fix":"Use sentence case and explain the benefit plainly.","evidence":"Brand guideline: tone"})
    return findings

st.title("🛡️ VeriBrand")
st.caption("Proof Before Publish · Brand governance review workspace")
st.success("Judge demo is ready — no sign-in, API key, database setup or installation is needed when using the deployed link.")
st.warning("Fictional AquaNest demo data only. Do not upload confidential, personal, customer or company-sensitive information.")
st.info(
    f"**Scope of this demo:** {BRAND.get('organisation','Demo organisation')} · "
    "PDF uploads support PDFs with selectable text only; scanned or image-only PDFs are not OCR-processed. "
    "Claim checking is a conservative, rules-based baseline using approved local facts and lexical matching — "
    "not an AI fact-checker or legal/compliance determination. "
    "The tool recommends findings, but **a human reviewer makes the final decision**."
)
st.caption("Review history is temporary session history for this browser/app session, not permanent storage.")
review, rules, history_tab = st.tabs(["① Review content", "② Approved evidence", "③ Review history"])

with review:
    col1, col2 = st.columns([1.2, .8])
    with col1:
        st.subheader("Submit content")
        kind = st.selectbox("Content type", ["Social media post", "Advertisement", "Email", "Document"])
        upload = st.file_uploader(
            "Upload a TXT, PDF or DOCX file (optional)",
            type=["txt", "pdf", "docx"],
            help="PDF support is for PDFs containing selectable text. Scanned or image-only PDFs are not supported because this demo does not perform OCR.",
        )
        demo_examples = {
            "Combined demo — multiple issues": "Meet the Aqua Nest PureFlow! Our BEST purifier guarantees 100% pure water. It includes a 9-stage filtration process and removes 100% of all harmful chemicals!!!",
            "Supported claim — approved 7-stage fact": "AquaNest PureFlow includes a 7-stage filtration process.",
            "Contradicted claim — 9 stages vs approved 7": "AquaNest PureFlow includes a 9-stage filtration process.",
            "Outdated evidence — old warranty source": "AquaNest PureFlow has a 2-year warranty.",
            "Unverified claim — no approved source": "AquaNest PureFlow removes 100% of all harmful chemicals.",
            "Product naming and tone": "Aqua Nest PureFlow is the BEST choice!!! BUY NOW!!!",
        }
        chosen_example = st.selectbox("Try a built-in example (optional)", list(demo_examples), key="demo_example")
        if st.button("Load selected example", use_container_width=True):
            st.session_state["content_input"] = demo_examples[chosen_example]
            st.session_state.result = None
            st.session_state.pop("loaded_upload", None)
            st.rerun()
        uploaded_type = None
        if upload:
            upload_fingerprint = (upload.name, hashlib.sha256(upload.getvalue()).hexdigest())
            try:
                extracted, uploaded_type = extract_uploaded_text(upload)
                st.success(f"Extracted text from {upload.name} ({uploaded_type}). Edit it below if needed.")
            except Exception as exc:
                st.error(f"Could not extract this file: {exc}")
                extracted = ""
            if st.session_state.get("loaded_upload") != upload_fingerprint:
                st.session_state["content_input"] = extracted
                st.session_state["loaded_upload"] = upload_fingerprint
        else:
            st.session_state.pop("loaded_upload", None)
        content = st.text_area("Content to review — paste text or edit extracted text", height=210, key="content_input")
        st.caption("No API key or external AI call is used. The current demo runs its configured rule and evidence checks locally.")
        if st.button("🔍 Analyse content", type="primary", use_container_width=True):
            if content.strip():
                current_facts = load_facts()
                current_findings = analyse(content, current_facts)
                st.session_state.result = {"kind":kind,"content":content,"findings":current_findings}
            else:
                st.warning("Enter content before analysing.")
    with col2:
        st.subheader("How to try VeriBrand")
        st.markdown("**1.** Choose a built-in example or upload a TXT, PDF or DOCX.\n\n**2.** Click **Analyse content**.\n\n**3.** Open each finding to inspect the rule, suggested correction and Claim Passport.\n\n**4.** Choose **Approved** or **Needs changes**, enter a reviewer label and save.")
        st.divider()
        st.subheader("What makes it different?")
        st.markdown("- **Claim Passport:** links factual claims to approved source, owner and validity date.\n- **Four evidence states:** Supported, Contradicted, Outdated and Unverified.\n- **Claim-checking scope:** a conservative rules-based baseline, not an AI fact-checker.\n- **Human decision:** the tool recommends findings; the human reviewer makes the final decision.\n- **Brand governance:** checks terminology, product naming, prohibited claims and tone - not just grammar.")
        st.caption("PDF support: PDFs containing selectable text. Scanned or image-only PDFs require OCR and are not supported.")
        st.warning("The tool recommends findings. An authorised human reviewer makes the final decision.")
        st.caption("The evidence engine is a conservative lexical baseline, not a legal or scientific fact-check. Always inspect the cited source. This is a functional hackathon demo, not a production compliance system.")
    r = st.session_state.result
    if r:
        st.divider()
        st.subheader("Review results")
        fs = r["findings"]
        a,b,c,d = st.columns(4)
        a.metric("Total findings",len(fs)); b.metric("High",sum(x["severity"]=="High" for x in fs)); c.metric("Medium",sum(x["severity"]=="Medium" for x in fs)); d.metric("Low",sum(x["severity"]=="Low" for x in fs))
        if not fs:
            st.success("No configured rule violations detected. Human approval is still required.")
        for i,x in enumerate(fs,1):
            with st.expander(f"{i}. {x['type']} · {x['severity']}", expanded=True):
                st.markdown(f"**Rule:** {x['rule']}\n\n**Detected:** {x['found']}\n\n**Why flagged:** {x['why']}\n\n**Suggested correction:** {x['fix']}")
                st.caption("Evidence status: " + x["evidence"])
                if x.get("type") == "Factual claim":
                    fact = x.get("source_fact") or {}
                    st.markdown("**Claim Passport**")
                    pc1, pc2, pc3 = st.columns(3)
                    pc1.metric("Evidence status", x.get("claim_status", "Unverified"))
                    pc2.write("**Source owner**")
                    pc2.write(fact.get("owner", "Not available"))
                    pc3.write("**Valid until**")
                    pc3.write(fact.get("valid_until", "Not available"))
                    st.caption(f"Source: {fact.get('source', 'No approved source matched')}")
        st.subheader("Human approval")
        decision = st.radio("Reviewer decision", ["Pending", "Approved", "Needs changes"], horizontal=True, key="decision")
        reviewer = st.text_input("Your reviewer label", "Judge / Demo reviewer", key="reviewer")
        note = st.text_input("Reviewer note (optional)", key="review_note")
        if st.button("Save review decision", type="primary", disabled=False):
            if decision == "Pending":
                st.error("Choose Approved or Needs changes.")
            else:
                item = {"time":datetime.now().strftime("%d %b %Y %I:%M %p"),"kind":r["kind"],"decision":decision,"reviewer":reviewer,"note":note,"findings":len(fs),"content":r["content"][:500]}
                st.session_state.demo_history.insert(0, item)
                st.session_state.result = None
                st.success("Review decision saved in this browser session.")
                st.rerun()

with rules:
    st.subheader("Approved brand guidelines")
    for x in BRAND.get("prohibited", []): st.markdown(f"- **Do not use “{x['phrase']}”.** {x['why']}")
    for x in BRAND.get("terminology", []): st.markdown(f"- Use **{x['use']}** instead of “{x['avoid']}”.")
    for x in BRAND.get("product_names", []): st.markdown(f"- Approved product name: **{x['right']}** (avoid “{x['wrong']}”).")
    st.divider()
    st.subheader("Approved facts knowledge base")
    facts = load_facts()
    if facts:
        for fact in facts:
            with st.container(border=True):
                st.markdown(f"**{fact['claim']}**")
                st.caption(f"Status: {fact.get('status','Approved')} · Source: {fact.get('source','')} · Owner: {fact.get('owner','')} · Valid until: {fact.get('valid_until','')}")
    else:
        st.info("No approved facts yet. Add a fact below.")
    st.info("This is a read-only fictional demo knowledge base. Judges can inspect the approved evidence records; no account or database setup is required.")

with history_tab:
    st.subheader("Human review history")
    st.caption("Review decisions are kept only for this browser session. Refreshing or closing the app may clear this demo history.")
    history = st.session_state.demo_history
    if not history:
        st.info("No decisions saved yet. Analyse content and save a reviewer decision to see it here.")
    for x in history:
        with st.container(border=True):
            st.markdown(f"**{x['decision']}** · {x['kind']} · {x['time']}")
            st.caption(f"Reviewer: {x['reviewer']} · Findings: {x['findings']}")
            st.write(x["content"])
            if x.get("note"):
                st.caption("Note: " + x["note"])

st.divider()
st.caption("VeriBrand Round 2 Judge Demo · Fictional data · No login, API key or database setup required · Rule-based evidence matching · Human approval remains final")

