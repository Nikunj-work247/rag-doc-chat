import json
import os
import uuid
from pathlib import Path

import requests
import streamlit as st

# ── Configuration & Paths ─────────────────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api")
HISTORY_DIR = Path(__file__).resolve().parents[1] / "data" / "chat_history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ── Custom Avatars (ChatGPT-Inspired SVG Base64) ────────────────────────────────
AI_AVATAR = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmci"
    "IHZpZXdCb3g9IjAgMCA0MCA0MCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIj48ZGVmcz48bGluZWFy"
    "R3JhZGllbnQgaWQ9ImFpR3JhZCIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+PH"
    "N0b3Agb2Zmc2V0PSIwJSIgc3RvcC1jb2xvcj0iIzEwYTM3ZiIvPjxzdG9wIG9mZnNldD0iMTAwJSIg"
    "c3RvcC1jb2xvcj0iIzBkOGM2YyIvPjwvbGluZWFyR3JhZGllbnQ+PC9kZWZzPjxyZWN0IHdpZHRoPS"
    "I0MCIgaGVpZ2h0PSI0MCIgcng9IjIwIiBmaWxsPSJ1cmwoI2FpR3JhZCkiLz48cGF0aCBkPSJNMjAg"
    "OSBDMjAuNiAxNC41IDI1LjUgMTkuNCAzMSAyMCBDMjUuNSAyMC42IDIwLjYgMjUuNSAyMCAzMSBDMT"
    "kuNCAyNS41IDE0LjUgMjAuNiA5IDIwIEMxNC41IDE5LjQgMTkuNCAxNC41IDIwIDkgWiIgZmlsbD0i"
    "I2ZmZmZmZiIvPjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjIuMiIgZmlsbD0iIzEwYTM3ZiIvPj"
    "wvc3ZnPg=="
)

USER_AVATAR = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmci"
    "IHZpZXdCb3g9IjAgMCA0MCA0MCIgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIj48ZGVmcz48bGluZWFy"
    "R3JhZGllbnQgaWQ9InVHcmFkIiB4MT0iMCUiIHkxPSIwJSIgeDI9IjEwMCUiIHkyPSIxMDAlIj48"
    "c3RvcCBvZmZzZXQ9IjAlIiBzdG9wLWNvbG9yPSIjNjM2NmYxIi8+PHN0b3Agb2Zmc2V0PSIxMDAl"
    "IiBzdG9wLWNvbG9yPSIjNDMzOGNhIi8+PC9saW5lYXJHcmFkaWVudD48L2RlZnM+PHJlY3Qgd2lk"
    "dGg9IjQwIiBoZWlnaHQ9IjQwIiByeD0iMjAiIGZpbGw9InVybCgjdUdyYWQpIi8+PGNpcmNsZSBj"
    "eD0iMjAiIGN5PSIxNSIgcj0iNS41IiBmaWxsPSIjZmZmZmZmIi8+PHBhdGggZD0iTTEwIDMxLjUg"
    "QzEwLjUgMjUuNSAxNC44IDIzIDIwIDIzIEMyNS4yIDIzIDI5LjUgMjUuNSAzMCAzMS41IFoiIGZp"
    "bGw9IiNmZmZmZmYiLz48L3N2Zz4="
)

st.set_page_config(
    page_title="DocChat AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bespoke ChatGPT Theme (CSS) ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Base Font & Canvas */
html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #ececec;
}

[data-testid="stAppViewContainer"] {
    background-color: #212121;
}

/* Constrain chat column width like ChatGPT/Claude */
.main .block-container {
    max-width: 820px !important;
    padding-top: 2rem !important;
    padding-bottom: 7rem !important;
    margin: 0 auto !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #171717 !important;
    border-right: 1px solid #2b2b2b !important;
}

[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Brand Banner */
.brand-box {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 12px;
    background: linear-gradient(180deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 20px;
}
.brand-logo {
    width: 34px;
    height: 34px;
    border-radius: 9px;
    background: linear-gradient(135deg, #10a37f 0%, #0d8c6c 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(16, 163, 127, 0.25);
}
.brand-name {
    font-size: 1.05rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.01em;
}
.brand-sub {
    font-size: 0.72rem;
    color: #9e9e9e;
    font-weight: 500;
}

/* Section Header */
.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8e8e8e;
    margin: 16px 0 8px 4px;
}

/* Document Pills */
.doc-card {
    display: flex;
    align-items: center;
    gap: 9px;
    background: #242424;
    border: 1px solid #333333;
    border-radius: 8px;
    padding: 7px 11px;
    margin-bottom: 6px;
    font-size: 0.8rem;
    color: #e5e5e5;
    transition: all 0.15s ease;
}
.doc-card:hover {
    border-color: #4a4a4a;
    background: #2a2a2a;
}
.doc-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.doc-size {
    font-size: 0.7rem;
    color: #737373;
    white-space: nowrap;
}

/* Main Chat Styling */
[data-testid="stChatMessage"] {
    background-color: transparent !important;
    border: none !important;
    padding: 1.25rem 0.5rem !important;
    max-width: 820px !important;
    margin: 0 auto !important;
}

/* User Bubble Enhancement */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
    background-color: #2f2f2f;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 10px 16px;
    display: inline-block;
    color: #f3f3f3;
}

/* Assistant Typography */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    border-bottom: 1px solid rgba(255,255,255,0.04) !important;
}

/* Source Badges */
.source-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.source-docs {
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.25);
}
.source-web {
    background: rgba(52, 211, 153, 0.1);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.25);
}

.query-hint {
    font-size: 0.75rem;
    color: #8c8c8c;
    font-style: italic;
    margin-bottom: 6px;
}

/* Source Card Container */
.source-box {
    background: #1c1c1c;
    border: 1px solid #2f2f2f;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
}
.source-box-title {
    font-size: 0.78rem;
    font-weight: 600;
    color: #60a5fa;
    margin-bottom: 3px;
}
.source-box-body {
    font-size: 0.76rem;
    color: #a3a3a3;
    line-height: 1.5;
}

/* Floating Input Box (Exact ChatGPT Look) */
[data-testid="stChatInputContainer"] {
    background: #2f2f2f !important;
    border: 1px solid #444444 !important;
    border-radius: 24px !important;
    padding: 6px 12px !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.35) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInputContainer"]:focus-within {
    border-color: #666666 !important;
    background: #333333 !important;
    box-shadow: 0 8px 36px rgba(0,0,0,0.5) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    border: none !important;
    color: #f5f5f5 !important;
    font-size: 0.95rem !important;
    line-height: 1.5 !important;
    padding: 8px 4px !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #888888 !important;
}
[data-testid="stChatInputSubmitButton"] button {
    background: #ffffff !important;
    color: #000000 !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: none !important;
    transition: transform 0.15s ease !important;
}
[data-testid="stChatInputSubmitButton"] button:hover {
    transform: scale(1.06) !important;
    background: #f0f0f0 !important;
}

/* Prompt Starter Cards (ChatGPT Home Hero) */
.hero-container {
    text-align: center;
    padding: 40px 10px 24px;
}
.hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.02em;
    margin-bottom: 6px;
}
.hero-subtitle {
    font-size: 0.9rem;
    color: #8c8c8c;
    margin-bottom: 24px;
}
.prompt-card {
    background: #2a2a2a;
    border: 1px solid #363636;
    border-radius: 12px;
    padding: 12px 14px;
    text-align: left;
    transition: all 0.2s ease;
    cursor: pointer;
    height: 100%;
}
.prompt-card:hover {
    border-color: #555555;
    background: #303030;
}
.prompt-card-title {
    font-size: 0.84rem;
    font-weight: 600;
    color: #f0f0f0;
    margin-bottom: 3px;
}
.prompt-card-desc {
    font-size: 0.74rem;
    color: #8a8a8a;
    line-height: 1.35;
}

/* Button & Scrollbar Overrides */
[data-testid="stButton"] > button {
    background-color: #2b2b2b !important;
    color: #e5e5e5 !important;
    border: 1px solid #3c3c3c !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
[data-testid="stButton"] > button:hover {
    background-color: #383838 !important;
    border-color: #525252 !important;
    color: #ffffff !important;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #171717; }
::-webkit-scrollbar-thumb { background: #333333; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #444444; }
</style>
""", unsafe_allow_html=True)


# ── Persistence Helpers ───────────────────────────────────────────────────────
def history_path(sid: str) -> Path:
    return HISTORY_DIR / f"{sid}.json"

def save_history(sid: str, messages: list) -> None:
    try:
        history_path(sid).write_text(json.dumps(messages, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def load_history(sid: str) -> list:
    p = history_path(sid)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def list_sessions() -> list[dict]:
    sessions = []
    for f in HISTORY_DIR.glob("*.json"):
        try:
            msgs = json.loads(f.read_text(encoding="utf-8"))
            if msgs:
                label = next((m["content"] for m in msgs if m["role"] == "user"), f.stem)
                sessions.append({
                    "sid": f.stem,
                    "label": label[:40],
                    "count": sum(1 for m in msgs if m["role"] == "user"),
                    "mtime": f.stat().st_mtime,
                })
        except Exception:
            pass
    return sorted(sessions, key=lambda x: x["mtime"], reverse=True)

def delete_session_history(sid: str) -> None:
    p = history_path(sid)
    if p.exists():
        p.unlink()


# ── Session State Management ──────────────────────────────────────────────────
params = st.query_params
if "sid" in params and "session_id" not in st.session_state:
    st.session_state.session_id = params["sid"]
    st.session_state.messages = load_history(params["sid"])
elif "session_id" not in st.session_state:
    new_sid = uuid.uuid4().hex[:10]
    st.session_state.session_id = new_sid
    st.session_state.messages = []
    st.query_params["sid"] = new_sid

if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.session_id)

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = ""


# ── API Helpers ───────────────────────────────────────────────────────────────
def check_backend_health() -> dict | None:
    try:
        resp = requests.get(f"{BACKEND_URL}/health", timeout=3)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def fetch_documents() -> list[dict]:
    try:
        resp = requests.get(f"{BACKEND_URL}/documents", timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []

def new_chat() -> None:
    try:
        requests.post(
            f"{BACKEND_URL}/chat/reset",
            json={"session_id": st.session_state.session_id},
            timeout=5,
        )
    except Exception:
        pass
    new_sid = uuid.uuid4().hex[:10]
    st.session_state.session_id = new_sid
    st.session_state.messages = []
    st.query_params["sid"] = new_sid

def switch_session(sid: str) -> None:
    try:
        requests.post(
            f"{BACKEND_URL}/chat/reset",
            json={"session_id": st.session_state.session_id},
            timeout=5,
        )
    except Exception:
        pass
    st.session_state.session_id = sid
    st.session_state.messages = load_history(sid)
    st.query_params["sid"] = sid

def fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n/1024:.1f} KB"
    return f"{n/1024**2:.1f} MB"

def doc_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {"pdf": "📄", "txt": "📝", "md": "📋"}.get(ext, "📎")


backend_info = check_backend_health()
is_online = backend_info is not None


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Minimalist Brand
    st.markdown("""
    <div class="brand-box">
        <div class="brand-logo">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
        </div>
        <div>
            <div class="brand-name">DocChat</div>
            <div class="brand-sub">AI Workspace</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat Actions (ChatGPT style)
    col1, col2 = st.columns([4, 1])
    with col1:
        st.button("＋ New Chat", on_click=new_chat, use_container_width=True)
    with col2:
        if st.button("🗑️", use_container_width=True, help="Clear active conversation"):
            delete_session_history(st.session_state.session_id)
            new_chat()
            st.rerun()

    # Recent Chats History
    all_sessions = list_sessions()
    if all_sessions:
        st.markdown('<div class="section-title">Recent Chats</div>', unsafe_allow_html=True)
        for s in all_sessions[:8]:
            is_active = s["sid"] == st.session_state.session_id
            indicator = "● " if is_active else ""
            btn_label = f"{indicator}{s['label']}"
            if st.button(btn_label, key=f"sess_{s['sid']}", use_container_width=True):
                switch_session(s["sid"])
                st.rerun()

    st.markdown("---")

    # Document Management
    st.markdown('<div class="section-title">Documents</div>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        st.markdown(f"📄 <span style='font-size:0.8rem; color:#a3a3a3;'>{len(uploaded_files)} file(s) selected</span>", unsafe_allow_html=True)
        if st.button("⚡ Add to Knowledge Base", use_container_width=True):
            if not is_online:
                st.error("Server connection unavailable.")
            else:
                with st.spinner("Processing documents..."):
                    files_payload = [
                        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                        for f in uploaded_files
                    ]
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/documents/upload",
                            files=files_payload,
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            chunks = data.get("total_chunks", 0)
                            st.success(f"Indexed {len(uploaded_files)} file(s) ({chunks} chunks)")
                            st.rerun()
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as exc:
                        st.error(f"Upload failed: {exc}")

    # Indexed Documents List
    existing_docs = fetch_documents()
    if existing_docs:
        for doc in existing_docs:
            icon = doc_icon(doc["filename"])
            size = fmt_bytes(doc.get("size_bytes", 0))
            st.markdown(
                f'<div class="doc-card">'
                f'<span>{icon}</span>'
                f'<span class="doc-name" title="{doc["filename"]}">{doc["filename"]}</span>'
                f'<span class="doc-size">{size}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No documents added yet.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT AREA
# ══════════════════════════════════════════════════════════════════════════════

def render_source_badge(source_type: str) -> None:
    if source_type == "web":
        st.markdown('<span class="source-pill source-web">🌐 Live Web Search</span>', unsafe_allow_html=True)
    elif source_type == "documents":
        st.markdown('<span class="source-pill source-docs">📄 Grounded Document</span>', unsafe_allow_html=True)

def render_sources(sources: list[dict], source_type: str = "documents") -> None:
    if not sources:
        return
    label = f"Referenced Sources ({len(sources)})"
    with st.expander(label):
        for i, src in enumerate(sources, 1):
            lbl = src.get("label", f"Reference {i}")
            text = src.get("text", "")
            st.markdown(
                f'<div class="source-box">'
                f'<div class="source-box-title">[{i}] {lbl}</div>'
                f'<div class="source-box-body">{text[:500]}{"…" if len(text) > 500 else ""}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ── Empty State / Prompt Cards (ChatGPT style) ────────────────────────────────
PROMPTS = [
    ("📑 Summarize Document", "Extract main takeaways, goals, and key findings.", "Summarise the main points of the uploaded documents."),
    ("🔑 Key Facts & Figures", "Retrieve crucial metrics, dates, and specifications.", "What are the most critical facts, numbers, and dates mentioned?"),
    ("💡 Actionable Insights", "Identify next steps, recommendations, or risks.", "What are the key recommendations or risks highlighted?"),
    ("🌐 Explore the Web", "Search the internet if documents do not cover it.", "Search the web for the latest developments regarding this topic."),
]

if not st.session_state.messages:
    st.markdown("""
    <div class="hero-container">
        <div class="hero-title">What would you like to know?</div>
        <div class="hero-subtitle">Ask questions about your documents, compare topics, or search the web.</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    for idx, (title, desc, query) in enumerate(PROMPTS):
        target_col = col_a if idx % 2 == 0 else col_b
        with target_col:
            st.markdown(
                f'<div class="prompt-card">'
                f'<div class="prompt-card-title">{title}</div>'
                f'<div class="prompt-card-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Ask this →", key=f"prompt_btn_{idx}", use_container_width=True):
                st.session_state.pending_prompt = query
                st.rerun()


# ── Replay Conversation History with Custom Avatars ────────────────────────────
for msg in st.session_state.messages:
    is_assistant = msg["role"] == "assistant"
    avatar = AI_AVATAR if is_assistant else USER_AVATAR

    with st.chat_message(msg["role"], avatar=avatar):
        if is_assistant:
            source_type = msg.get("source_type", "")
            if source_type:
                render_source_badge(source_type)
            if msg.get("searched_for"):
                st.markdown(
                    f'<div class="query-hint">Refined query: <em>"{msg["searched_for"]}"</em></div>',
                    unsafe_allow_html=True,
                )

        content = msg.get("content", "")
        if content:
            st.markdown(content)
        else:
            st.warning("No answer was generated.")

        if is_assistant:
            render_sources(msg.get("sources", []), msg.get("source_type", "documents"))


# ── Chat Input Bar ─────────────────────────────────────────────────────────────
pending = st.session_state.pop("pending_prompt", "") if st.session_state.get("pending_prompt") else ""

prompt = st.chat_input("Message DocChat AI…") or pending

if prompt:
    prompt = prompt.strip()
    if not prompt:
        st.stop()

    if not is_online:
        st.error("⚠️ Backend server is offline. Please start FastAPI (`python scripts/run_api.py`).")
        st.stop()

    # Append & display User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Call Backend API & stream Assistant response
    with st.chat_message("assistant", avatar=AI_AVATAR):
        def stream_generator():
            try:
                with requests.post(
                    f"{BACKEND_URL}/chat/stream",
                    json={"question": prompt, "session_id": st.session_state.session_id},
                    stream=True,
                    timeout=120,
                ) as resp:
                    if resp.status_code != 200:
                        yield f"Backend error ({resp.status_code}): {resp.text}"
                        return
                    for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk
            except Exception as exc:
                yield f"Connection error: {exc}"

        answer = st.write_stream(stream_generator())

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": [],
        "searched_for": "",
        "source_type": "",
    })
    save_history(st.session_state.session_id, st.session_state.messages)
