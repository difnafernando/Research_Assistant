import re
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
import streamlit as st
from groq import Groq

# ── Research Reader helpers ───────────────────────────────────────────────────
def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF file."""
    try:
        import pypdf
        reader = pypdf.PdfReader(uploaded_file)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((i + 1, text))
        return pages
    except Exception as e:
        return None

SECTION_CATEGORIES = {
    "📌 Abstract": ["abstract", "summary"],
    "🔬 Introduction": ["introduction", "intro", "background", "motivation"],
    "📐 Methodology": ["method", "methodology", "approach", "experiment", "procedure", "technique", "design"],
    "📊 Results": ["result", "finding", "outcome", "performance", "evaluation", "analysis"],
    "💬 Discussion": ["discussion", "interpretation", "implication"],
    "🏁 Conclusion": ["conclusion", "concluding", "future work", "limitation", "remark"],
    "📚 References": ["reference", "bibliography", "citation"],
}

def detect_section(heading_text):
    lower = heading_text.lower()
    for label, keywords in SECTION_CATEGORIES.items():
        if any(k in lower for k in keywords):
            return label
    return "📄 Other"

# ── History Storage ───────────────────────────────────────────────────────────
HISTORY_DIR = Path(__file__).parent / "chat_history"
HISTORY_DIR.mkdir(exist_ok=True)

def save_chat(session_id, messages, mode):
    if not messages:
        return
    title = next((m["content"][:50] for m in messages if m["role"] == "user"), "Untitled")
    data = {
        "id": session_id,
        "title": title,
        "mode": mode,
        "timestamp": datetime.now().isoformat(),
        "messages": messages,
    }
    with open(HISTORY_DIR / f"{session_id}.json", "w") as f:
        json.dump(data, f, indent=2)

def load_all_chats():
    chats = []
    for f in sorted(HISTORY_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            with open(f) as fp:
                chats.append(json.load(fp))
        except Exception:
            pass
    return chats

def delete_chat(session_id):
    p = HISTORY_DIR / f"{session_id}.json"
    if p.exists():
        p.unlink()

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Scholar AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:     #0c0f1a;
    --card:   #131826;
    --border: rgba(99,179,237,0.15);
    --accent: #63b3ed;
    --purple: #b794f4;
    --text:   #e2e8f0;
    --muted:  #718096;
    --radius: 14px;
}
html, body, [class*="css"] { font-family: 'Sora', sans-serif !important; background: var(--bg) !important; color: var(--text); }
.stApp {
    background: radial-gradient(ellipse at 15% 30%, rgba(99,179,237,0.07) 0%, transparent 55%),
                radial-gradient(ellipse at 85% 70%, rgba(183,148,244,0.06) 0%, transparent 55%),
                var(--bg);
}
[data-testid="stSidebar"] { background: var(--card) !important; border-right: 1px solid var(--border) !important; }
[data-testid="stSidebar"] * { color: var(--text) !important; }

.hero { text-align: center; padding: 2rem 1rem 1rem; }
.hero h1 {
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0, #63b3ed, #b794f4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
}
.hero p { color: var(--muted); font-size: 0.9rem; margin-top: 0.4rem; font-weight: 300; }

.mode-badge {
    display: inline-block; background: rgba(99,179,237,0.1);
    border: 1px solid rgba(99,179,237,0.3); border-radius: 20px;
    padding: 0.2rem 0.9rem; font-size: 0.75rem; color: var(--accent);
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.6rem;
}
.bubble-user {
    background: linear-gradient(135deg, #2b6cb0, #3182ce); color: #fff;
    padding: 0.8rem 1.1rem; border-radius: 16px 16px 4px 16px;
    max-width: 70%; margin-left: auto; font-size: 0.9rem; line-height: 1.6;
    margin-bottom: 1rem; box-shadow: 0 4px 15px rgba(49,130,206,0.3);
}
.bubble-ai {
    background: var(--card); border: 1px solid var(--border); color: var(--text);
    padding: 0.9rem 1.2rem; border-radius: 16px 16px 16px 4px;
    max-width: 80%; font-size: 0.9rem; line-height: 1.7;
    margin-bottom: 0.3rem; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.bubble-ai code {
    font-family: 'JetBrains Mono', monospace;
    background: rgba(99,179,237,0.1); border: 1px solid rgba(99,179,237,0.2);
    padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.82rem; color: #90cdf4;
}
.msg-row-user { display: flex; justify-content: flex-end; align-items: flex-end; gap: 0.5rem; margin: 0.5rem 0; }
.msg-row-ai   { display: flex; justify-content: flex-start; align-items: flex-end; gap: 0.5rem; margin: 0.5rem 0; }
.avatar { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; flex-shrink: 0; }
.av-user { background: linear-gradient(135deg, #3182ce, #805ad5); }
.av-ai   { background: var(--card); border: 1px solid var(--border); }

/* History item */
.hist-item {
    background: rgba(99,179,237,0.05);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.55rem 0.8rem;
    margin-bottom: 0.4rem;
    cursor: pointer;
    transition: all 0.18s;
}
.hist-item:hover { background: rgba(99,179,237,0.12); border-color: rgba(99,179,237,0.35); }
.hist-title { font-size: 0.8rem; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.hist-meta  { font-size: 0.68rem; color: var(--muted); margin-top: 0.15rem; }

.welcome { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.8rem; text-align: center; margin: 0.5rem 0 1.5rem; }
.welcome h3 { font-size: 1.2rem; margin-bottom: 0.4rem; }
.welcome p  { color: var(--muted); font-size: 0.85rem; line-height: 1.6; margin: 0; }

.stButton > button {
    background: linear-gradient(135deg, #2b6cb0, #3182ce) !important; color: #fff !important;
    border: none !important; border-radius: 9px !important; font-family: 'Sora', sans-serif !important;
    font-weight: 500 !important; padding: 0.5rem 1.1rem !important; transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 5px 15px rgba(49,130,206,0.35) !important; }
.stTextInput input, .stTextArea textarea {
    background: var(--card) !important; border: 1px solid var(--border) !important;
    border-radius: 10px !important; color: var(--text) !important; font-family: 'Sora', sans-serif !important;
}
.stRadio label { font-size: 0.88rem !important; color: var(--text) !important; }
hr { border-color: var(--border) !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
.stat-row { display: flex; gap: 0.8rem; justify-content: center; margin-top: 0.5rem; }
.stat-chip { background: rgba(99,179,237,0.08); border: 1px solid rgba(99,179,237,0.2); border-radius: 10px; padding: 0.4rem 0.9rem; text-align: center; }
.stat-chip .val { font-size: 1.2rem; font-weight: 600; color: var(--accent); }
.stat-chip .lbl { font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }

/* Research Reader */
.reader-hero { text-align: center; padding: 1.8rem 1rem 0.8rem; }
.reader-hero h1 { font-size: 2.2rem; font-weight: 700;
    background: linear-gradient(135deg, #e2e8f0, #68d391, #63b3ed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin:0; }
.reader-hero p { color: var(--muted); font-size:0.88rem; margin-top:0.3rem; }
.section-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.section-card h3 { font-size:1rem; font-weight:600; color: var(--accent); margin:0 0 0.6rem; }
.section-card p  { font-size:0.88rem; color: var(--text); line-height:1.7; margin:0; white-space:pre-wrap; }
.pdf-badge {
    display:inline-block; background:rgba(104,211,145,0.12);
    border:1px solid rgba(104,211,145,0.35); border-radius:20px;
    padding:0.2rem 1rem; font-size:0.75rem; color:#68d391;
    letter-spacing:0.07em; text-transform:uppercase; margin-bottom:1rem;
}
.upload-box {
    background: var(--card); border: 2px dashed rgba(99,179,237,0.3);
    border-radius: var(--radius); padding: 2.5rem 1.5rem; text-align:center;
    margin: 1rem 0;
}
.upload-box p { color: var(--muted); font-size:0.9rem; margin:0.4rem 0 0; }
</style>
""", unsafe_allow_html=True)

# ── System Prompts ────────────────────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "🔬 Research": """You are Scholar AI, an expert research assistant for university students.
Provide thorough, well-structured answers. Use markdown formatting with headers and bullet points.
Include real-world examples, mention key researchers or papers when relevant, and always explain WHY something matters.
End complex answers with: "Want me to go deeper into any part of this?" """,

    "💡 Explain": """You are Scholar AI in EXPLAIN mode.
Always follow this structure:
1. One plain-English sentence definition
2. An everyday analogy
3. Step-by-step breakdown
4. A concrete example
5. Key takeaway in one line
Avoid jargon unless you define it. Be enthusiastic and encouraging.""",

    "📝 Quiz Me": """You are Scholar AI in QUIZ mode.
When given a topic: generate 4 questions (1 easy, 2 medium, 1 hard).
After the user answers: score each response, explain what was right/wrong, and give a final score out of 4.
Be encouraging and explain misconceptions clearly.""",

    "⚖️ Critique": """You are Scholar AI in CRITIQUE mode.
Structure every response as:
## ✅ Strengths
## ⚠️ Weaknesses / Limitations
## 🔄 Alternatives
## 🧭 Verdict
Be balanced, cite evidence, and be intellectually honest.""",
}

# ── Session State ─────────────────────────────────────────────────────────────
if "messages"   not in st.session_state: st.session_state.messages   = []
if "mode"       not in st.session_state: st.session_state.mode       = "🔬 Research"
if "session_id" not in st.session_state: st.session_state.session_id = str(uuid.uuid4())
if "view"       not in st.session_state: st.session_state.view       = "chat"   # "chat", "history", or "reader"
if "pdf_sections"   not in st.session_state: st.session_state.pdf_sections   = {}
if "pdf_full_text"  not in st.session_state: st.session_state.pdf_full_text  = ""
if "pdf_name"       not in st.session_state: st.session_state.pdf_name       = ""
if "pdf_summary"    not in st.session_state: st.session_state.pdf_summary    = {}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1.2rem 0 0.8rem;'>
        <div style='font-size:2.2rem;'>🎓</div>
        <div style='font-size:1.05rem; font-weight:600; color:#e2e8f0;'>Scholar AI</div>
        <div style='font-size:0.72rem; color:#718096; letter-spacing:0.1em; text-transform:uppercase;'>Research Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    api_key = st.text_input("🔑 Groq API Key", type="password", placeholder="gsk_...")
    if api_key:
        st.success("✅ Key saved for this session")

    st.divider()

    # New Chat button
    if st.button("✏️ New Chat", use_container_width=True):
        # Save current chat before clearing
        if st.session_state.messages:
            save_chat(st.session_state.session_id, st.session_state.messages, st.session_state.mode)
        st.session_state.messages   = []
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.view       = "chat"
        st.rerun()

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # Toggle history panel
    hist_label = "📚 Chat History" if st.session_state.view != "history" else "💬 Back to Chat"
    if st.button(hist_label, use_container_width=True):
        st.session_state.view = "history" if st.session_state.view != "history" else "chat"
        st.rerun()

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # Research Reader button
    reader_label = "🔭 Research Reader" if st.session_state.view != "reader" else "💬 Back to Chat"
    if st.button(reader_label, use_container_width=True):
        st.session_state.view = "reader" if st.session_state.view != "reader" else "chat"
        st.rerun()

    st.divider()

    st.markdown("<p style='font-size:0.78rem; color:#718096; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.5rem;'>Study Mode</p>", unsafe_allow_html=True)
    mode = st.radio("", list(SYSTEM_PROMPTS.keys()), index=0, label_visibility="collapsed")
    st.session_state.mode = mode

    st.divider()

    n_user = sum(1 for m in st.session_state.messages if m["role"] == "user")
    n_ai   = len(st.session_state.messages) - n_user
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-chip"><div class="val">{n_user}</div><div class="lbl">Questions</div></div>
        <div class="stat-chip"><div class="val">{n_ai}</div><div class="lbl">Answers</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("<p style='font-size:0.7rem; color:#4a5568; text-align:center; margin-top:1rem;'>Powered by Groq · LLaMA 3.3</p>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# RESEARCH READER VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "reader":
    st.markdown("""
    <div class="reader-hero">
        <h1>🔭 Research Reader</h1>
        <p>Upload a research paper PDF — get instant structured summaries by section</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar to use Research Reader.")
        st.stop()

    # ── Upload Area ──────────────────────────────────────────────────────────
    uploaded_pdf = st.file_uploader(
        "Upload Research Paper (PDF)",
        type=["pdf"],
        label_visibility="collapsed",
        key="pdf_uploader",
    )

    if uploaded_pdf is not None and uploaded_pdf.name != st.session_state.pdf_name:
        # New PDF uploaded — reset state
        st.session_state.pdf_name = uploaded_pdf.name
        st.session_state.pdf_sections = {}
        st.session_state.pdf_summary = {}
        st.session_state.pdf_full_text = ""

        with st.spinner("📄 Extracting text from PDF…"):
            pages = extract_pdf_text(uploaded_pdf)

        if not pages:
            st.error("❌ Could not extract text from this PDF. It may be scanned or image-based.")
            st.stop()

        # Combine all text and try to split by headings
        full_text = "\n".join(text for _, text in pages)
        st.session_state.pdf_full_text = full_text

        # Heuristic section detection: lines that are short, ALL-CAPS or Title Case followed by body
        import re as _re
        heading_pattern = _re.compile(
            r'^(?:\d+\.?\s+)?([A-Z][A-Z\s\-]{2,60}|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,6})\s*$',
            _re.MULTILINE
        )
        matches = list(heading_pattern.finditer(full_text))
        raw_sections = {}
        for i, m in enumerate(matches):
            heading = m.group(0).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            body = full_text[start:end].strip()
            if len(body) > 80:  # skip tiny sections
                category = detect_section(heading)
                if category not in raw_sections:
                    raw_sections[category] = []
                raw_sections[category].append(f"**{heading}**\n{body}")

        # Fallback: if no sections detected, treat whole text as one block
        if not raw_sections:
            raw_sections["📄 Full Paper"] = [full_text]

        st.session_state.pdf_sections = raw_sections

        # ── AI Summarise each category ──────────────────────────────────────
        client = Groq(api_key=api_key)
        summaries = {}

        system_prompt = """You are an expert academic summarizer.
When given a section of a research paper, provide a clear, concise summary in 3-5 sentences.
Focus on the key contributions, methods, findings, or arguments.
Use plain English — avoid unnecessary jargon.
Do NOT use bullet points; write flowing prose."""

        progress = st.progress(0, text="🤖 Summarizing sections with AI…")
        categories = list(raw_sections.keys())

        for idx, cat in enumerate(categories):
            combined = "\n\n".join(raw_sections[cat])[:4000]  # cap tokens
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Summarize this section of the paper:\n\n{combined}"}
                    ],
                    temperature=0.4,
                    max_tokens=400,
                )
                summaries[cat] = resp.choices[0].message.content.strip()
            except Exception as e:
                summaries[cat] = f"⚠️ Could not summarize: {e}"
            progress.progress((idx + 1) / len(categories), text=f"🤖 Summarizing {cat}…")

        progress.empty()
        st.session_state.pdf_summary = summaries
        st.rerun()

    # ── Display Results ──────────────────────────────────────────────────────
    if st.session_state.pdf_name and st.session_state.pdf_summary:
        st.markdown(f'<div class="pdf-badge">📄 {st.session_state.pdf_name}</div>', unsafe_allow_html=True)

        # Overall summary button
        if st.button("🌐 Generate Overall Summary", use_container_width=False):
            with st.spinner("Generating overall summary…"):
                client = Groq(api_key=api_key)
                snippet = st.session_state.pdf_full_text[:6000]
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert academic summarizer. Provide a comprehensive 6-8 sentence overview of this research paper covering: the problem being solved, the methodology used, key findings, and implications. Write in clear, engaging prose."},
                        {"role": "user", "content": f"Summarize this research paper:\n\n{snippet}"}
                    ],
                    temperature=0.4,
                    max_tokens=600,
                )
                overall = resp.choices[0].message.content.strip()
                st.session_state.pdf_summary["🌐 Overall Summary"] = overall
                st.rerun()

        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

        # Section selector tabs
        available = list(st.session_state.pdf_summary.keys())
        priority_order = ["🌐 Overall Summary", "📌 Abstract", "🔬 Introduction",
                          "📐 Methodology", "📊 Results", "💬 Discussion",
                          "🏁 Conclusion", "📚 References", "📄 Other", "📄 Full Paper"]
        ordered = [s for s in priority_order if s in available] + [s for s in available if s not in priority_order]

        selected_sections = st.multiselect(
            "Select sections to view:",
            options=ordered,
            default=ordered[:min(4, len(ordered))],
            label_visibility="visible",
        )

        for section in selected_sections:
            summary = st.session_state.pdf_summary.get(section, "")
            raw_text = "\n\n".join(st.session_state.pdf_sections.get(section, []))
            st.markdown(f"""
            <div class="section-card">
                <h3>{section}</h3>
                <p>{summary}</p>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📋 View raw text — {section}"):
                st.text_area("", value=raw_text[:3000] + ("…" if len(raw_text) > 3000 else ""),
                             height=200, label_visibility="collapsed", key=f"raw_{section}")

        st.divider()

        # Ask a question about the paper
        st.markdown("<p style='font-size:0.9rem; color:#718096;'>💬 Ask a question about this paper</p>", unsafe_allow_html=True)
        paper_question = st.chat_input("e.g. What dataset did they use? What are the limitations?", key="reader_chat")
        if paper_question:
            with st.spinner("Answering…"):
                client = Groq(api_key=api_key)
                context = st.session_state.pdf_full_text[:7000]
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert research assistant. Answer questions about the provided research paper accurately and concisely, citing specific sections where possible."},
                        {"role": "user", "content": f"Paper content:\n{context}\n\nQuestion: {paper_question}"}
                    ],
                    temperature=0.5,
                    max_tokens=600,
                )
                answer = resp.choices[0].message.content.strip()
            st.markdown(f"""
            <div class="section-card" style="border-color:rgba(99,179,237,0.4);">
                <h3>❓ {paper_question}</h3>
                <p>{answer}</p>
            </div>
            """, unsafe_allow_html=True)

    elif not uploaded_pdf:
        st.markdown("""
        <div class="upload-box">
            <div style='font-size:2.5rem;'>📄</div>
            <p>Drag and drop a research paper PDF above, or click to browse</p>
            <p style='font-size:0.78rem; margin-top:0.8rem; color:#4a5568;'>
                Supports standard text-based PDFs · Section detection is automatic
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# HISTORY VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.view == "history":
    st.markdown("""
    <div class="hero">
        <h1>📚 Chat History</h1>
        <p>All your past conversations — click one to continue</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    all_chats = load_all_chats()

    if not all_chats:
        st.info("No saved chats yet. Start a conversation and it will appear here.")
    else:
        for chat in all_chats:
            ts = datetime.fromisoformat(chat["timestamp"]).strftime("%b %d, %Y  %H:%M")
            msg_count = len([m for m in chat["messages"] if m["role"] == "user"])

            col_main, col_del = st.columns([0.88, 0.12])
            with col_main:
                if st.button(
                    f"**{chat['title']}{'...' if len(chat['title']) >= 50 else ''}**\n\n"
                    f"_{chat['mode']}  ·  {msg_count} question{'s' if msg_count != 1 else ''}  ·  {ts}_",
                    key=f"load_{chat['id']}",
                    use_container_width=True,
                ):
                    # Save current chat first
                    if st.session_state.messages:
                        save_chat(st.session_state.session_id, st.session_state.messages, st.session_state.mode)
                    # Load selected chat
                    st.session_state.messages   = chat["messages"]
                    st.session_state.session_id = chat["id"]
                    st.session_state.mode       = chat["mode"]
                    st.session_state.view       = "chat"
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del_{chat['id']}", help="Delete this chat"):
                    delete_chat(chat["id"])
                    st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# CHAT VIEW
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="hero">
    <div class="mode-badge">Mode: {mode}</div>
    <h1>🎓 Scholar AI</h1>
    <p>Your intelligent research & study companion — ask me anything</p>
</div>
""", unsafe_allow_html=True)

st.divider()

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome">
        <h3>👋 Welcome! How can I help you today?</h3>
        <p>Pick a mode from the sidebar, then ask anything.<br>
        I can research topics, explain concepts, quiz you, or critique ideas.</p>
    </div>
    """, unsafe_allow_html=True)

    examples = {
        "🔬 Research":  ["What are transformer models?", "Explain reinforcement learning", "How does CRISPR work?"],
        "💡 Explain":   ["Explain gradient descent simply", "What is the p-value?", "How does backpropagation work?"],
        "📝 Quiz Me":   ["Quiz me on machine learning", "Test me on Python basics", "Quiz me on statistics"],
        "⚖️ Critique":  ["Critique decision trees", "What are LLM limitations?", "Weaknesses of k-means clustering"],
    }
    prompts = examples.get(st.session_state.mode, examples["🔬 Research"])
    cols = st.columns(3)
    for col, prompt in zip(cols, prompts):
        with col:
            if st.button(prompt, use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": prompt})
                st.rerun()

# Render messages
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(f"""
        <div class="msg-row-user">
            <div class="bubble-user">{msg['content']}</div>
            <div class="avatar av-user">👤</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        clean = re.sub(r'#{1,6}\s*', '', msg["content"])
        clean = re.sub(r'\*+', '', clean)
        display = clean.replace("\n", "<br>")
        col1, col2 = st.columns([0.05, 0.95])
        with col1:
            st.markdown('<div class="avatar av-ai" style="margin-top:0.6rem">🎓</div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="bubble-ai">{display}</div>', unsafe_allow_html=True)
            with st.expander("📋 Copy answer", expanded=False):
                st.code(msg["content"], language=None)

st.divider()

# ── Chat Input ────────────────────────────────────────────────────────────────
placeholders = {
    "🔬 Research":  "Ask me to research any topic…",
    "💡 Explain":   "What concept should I explain?",
    "📝 Quiz Me":   "Tell me a subject to quiz you on…",
    "⚖️ Critique":  "What should I critique or analyze?",
}

user_input = st.chat_input(placeholders.get(st.session_state.mode, "Ask me anything…"))

if user_input:
    if not api_key:
        st.error("⚠️ Please enter your Groq API key in the sidebar first.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": user_input})

    api_messages = [{"role": "system", "content": SYSTEM_PROMPTS[st.session_state.mode]}]
    for m in st.session_state.messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    with st.spinner("Thinking…"):
        try:
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=api_messages,
                temperature=0.6,
                max_tokens=2048,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"⚠️ Error: {str(e)}\n\nCheck your API key and try again."

    st.session_state.messages.append({"role": "assistant", "content": answer})

    # Auto-save after every reply
    save_chat(st.session_state.session_id, st.session_state.messages, st.session_state.mode)

    st.rerun()
