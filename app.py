"""Small educational refund/return guide. Run with streamlit run app.py."""

import os
from pathlib import Path
from urllib.parse import urlsplit

import streamlit as st

from core import answer_question, complaint_draft, load_sources


st.set_page_config(page_title="Resolve · India refund guide", page_icon="📋")
st.title("Resolve · India refund & return guide")
st.warning(
    "Educational prototype — not legal advice. This guide does not establish "
    "retailer policies, eligibility for a refund, or guaranteed deadlines."
)
st.caption("Check the linked official information and the terms relevant to your purchase.")

ai_configured = bool(os.environ.get("OPENAI_API_KEY", "").strip()) and bool(
    os.environ.get("OPENAI_MODEL", "").strip()
)

with st.sidebar:
    st.header("About this demo")
    st.write("India-focused public-information summaries and a draft you can edit.")
    st.write(
        "AI configuration: "
        + ("key and model environment variables are set." if ai_configured else
           "incomplete; AI is unavailable until both environment variables are set.")
    )
    st.caption(
        "Set OPENAI_API_KEY and OPENAI_MODEL in the server environment. "
        "The app does not automatically load .env files. Configuration presence "
        "does not verify provider access."
    )
    st.info(
        "Local / small private demo only. AI requests may incur costs and provider "
        "rate limits. A public release needs authentication and rate limits."
    )
    st.write(
        "There is no app database. Questions and drafts may remain in this active "
        "session; the hosting platform and AI provider may retain content or "
        "metadata under their policies. Complete privacy is not guaranteed."
    )


def source_link(url):
    """Link only to curated Indian government/consumer commission hosts."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        allowed = (
            host.endswith(".gov.in")
            or host.endswith(".nic.in")
            or host in {"gov.in", "nic.in"}
        )
        if parsed.scheme == "https" and allowed and not parsed.username and not parsed.password:
            return url
    except ValueError:
        pass
    return None


try:
    sources = load_sources(Path(__file__).parent / "data" / "sources.json")
    corpus_ready = bool(sources)
except Exception:
    sources = []
    corpus_ready = False

if not corpus_ready:
    st.error(
        "The public-source collection could not be loaded or is empty. "
        "Please ask the operator to check the bundled sources file. "
        "Question answering is unavailable; you can still prepare a draft below."
    )

st.header("Ask a question")
st.write(
    "Keep it general. Do not enter names, addresses, order numbers, payment details, "
    "passwords, or other sensitive information."
)
st.info(
    "AI is optional and off by default. Enabling AI and submitting sends your "
    "question and public-source summaries to OpenAI. Do not include sensitive information."
)
with st.form("question_form"):
    question = st.text_area(
        "What would you like to understand?", max_chars=2000,
        placeholder="What general steps can I consider if a refund has not arrived?",
    )
    use_ai = st.checkbox("Use OpenAI for this answer", value=False, disabled=not ai_configured)
    ask = st.form_submit_button("Get guidance", disabled=not corpus_ready)

if ask:
    st.session_state.pop("guidance", None)
    if not question.strip():
        st.warning("Enter a general refund or return question first.")
    else:
        try:
            with st.spinner("Preparing guidance…"):
                result = answer_question(question.strip(), sources, use_ai=use_ai and ai_configured)
            if not isinstance(result, dict) or not isinstance(result.get("answer"), str):
                raise ValueError("Invalid answer")
            st.session_state["guidance"] = result
        except Exception:
            st.error("Guidance is temporarily unavailable. Try again later or consult the official sources directly.")

result = st.session_state.get("guidance")
if result and corpus_ready:
    st.subheader("Guidance")
    st.text(result["answer"])
    st.text("Answer mode: " + str(result.get("mode", "unspecified")))
    if result.get("warning"):
        st.text("Notice: " + str(result["warning"]))
    st.subheader("Sources used")
    st.caption("These are public-information summaries, not quotations. Review dates are not promises that a source is current.")
    result_sources = result.get("sources", [])
    if not result_sources:
        st.text("No matching sources were returned. Do not treat this answer as verified guidance.")
    # Resolve returned IDs against the local corpus; never use AI-generated URLs.
    trusted = {str(item.get("id")): item for item in sources if isinstance(item, dict)}
    for item in result_sources:
        if not isinstance(item, dict):
            continue
        source = trusted.get(str(item.get("id")))
        if not source:
            continue
        with st.container(border=True):
            st.text(str(source.get("title", "Public source")))
            st.text("Reviewed on: " + str(source.get("reviewed_on", "not provided")))
            st.text("Country: " + str(source.get("country", "India")))
            st.text("Source type: " + str(source.get("kind", "not provided")))
            st.text("Summary (not a quotation):\n" + str(source.get("text", "")))
            url = source_link(source.get("url"))
            if url:
                st.link_button("Read official source", url)
            else:
                st.text("A verified official HTTPS link is not available for this entry.")

st.header("Practical checklist")
st.caption("App suggestions — not official requirements or a guarantee of resolution.")
st.text(
    "• Review the purchase terms and the seller’s current return/refund policy.\n"
    "• Keep relevant receipts and correspondence securely outside this demo.\n"
    "• Describe the issue clearly and ask the seller for a written response.\n"
    "• Check official channels for current guidance on next steps."
)

st.header("Prepare a complaint draft")
st.write("Use a retailer’s business name and a generic issue only. Do not enter personal or order details.")
with st.form("draft_form"):
    retailer = st.text_input("Retailer / business name", max_chars=150)
    issue = st.text_area("Brief issue (no personal details)", max_chars=2000)
    make_draft = st.form_submit_button("Create draft locally")

if make_draft:
    if not retailer.strip() or not issue.strip():
        st.warning("Enter a business name and a brief general description.")
    else:
        try:
            draft = complaint_draft(retailer.strip(), issue.strip())
            if not isinstance(draft, str):
                raise ValueError("Invalid draft")
            st.session_state["editable_draft"] = draft
        except Exception:
            st.error("The draft could not be prepared. Please try again later.")

if "editable_draft" in st.session_state:
    st.text_area("Review and edit your draft (keep personal details out)", key="editable_draft", height=300)
    st.caption("Finish any personal details outside this demo. Nothing is sent automatically.")
    st.download_button(
        "Download draft as text", data=st.session_state["editable_draft"],
        file_name="complaint-draft.txt", mime="text/plain",
    )
