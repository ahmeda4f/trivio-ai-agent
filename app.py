import os
import uuid
import html
import logging
import requests
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import streamlit as st

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Trivio-Magdy-UI")

API_TIMEOUT = 90
MAX_RETRIES = 3

st.set_page_config(
page_title="Trivio | عم مجدي - Football AI",
page_icon="⚽",
layout="wide",
initial_sidebar_state="expanded",
)

try:
CHAT_ENDPOINT = st.secrets.get("CHAT_ENDPOINT", "")
except FileNotFoundError:
CHAT_ENDPOINT = os.getenv("CHAT_ENDPOINT", "")

@st.cache_resource
def get_api_session() -> requests.Session:
session = requests.Session()
retry_strategy = Retry(
total=MAX_RETRIES,
backoff_factor=1,
status_forcelist=[429, 500, 502, 503, 504],
allowed_methods=["POST", "GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
return session

def ask_backend(session_id: str, message: str) -> str:
session = get_api_session()
payload = {"id": session_id, "message": message}

logger.info(f"Sending prompt to Magdy API for session: {session_id[:8]}...")

response = session.post(
    url=CHAT_ENDPOINT,
    json=payload,
    timeout=API_TIMEOUT
)
response.raise_for_status()

data = response.json()
if "message" not in data:
    logger.error("API response missing 'message' key.")
    raise ValueError("Invalid response format from backend.")
    
return str(data["message"])

def initialize_session():
if "session_id" not in st.session_state:
st.session_state.session_id = str(uuid.uuid4())
logger.info(f"New session initialized: {st.session_state.session_id}")

if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "pending_question" not in st.session_state:
    st.session_state.pending_question = None

def reset_conversation():
st.session_state.session_id = str(uuid.uuid4())
st.session_state.messages = []
st.session_state.pending_question = None
st.toast("تم بدء محادثة جديدة بنجاح!", icon="🔄")
logger.info("Conversation reset by user.")

def inject_custom_css():
st.markdown(
"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; }
    body { background: #06100b; }
    
    .stApp {
        background: radial-gradient(circle at 50% -15%, rgba(25, 170, 100, 0.14), transparent 34%), #06100b;
        color: #edf5f0;
    }

    #MainMenu, footer, header { visibility: hidden; }
    .block-container { max-width: 1100px; padding-top: 1.2rem; padding-bottom: 6rem; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #08150e 0%, #06100b 100%);
        border-left: 1px solid rgba(255,255,255,0.045);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
    .sidebar-brand { display: flex; align-items: center; gap: 12px; padding: 4px 8px 26px; direction: ltr; }
    .sidebar-logo {
        width: 44px; height: 44px; min-width: 44px; border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(145deg, #19b36b, #087440);
        box-shadow: 0 10px 30px rgba(18, 170, 99, 0.20); font-size: 21px;
    }
    .sidebar-brand-title { color: #ffffff; font-size: 18px; font-weight: 800; line-height: 1.1; }
    .sidebar-brand-subtitle { color: #6f8378; font-size: 10px; margin-top: 4px; letter-spacing: 0.3px; }
    
    .sidebar-label { color: #63776c; font-size: 10px; font-weight: 700; letter-spacing: 0.7px; margin: 22px 8px 9px; direction: rtl; text-align: right; }
    .sidebar-description {
        margin: 20px 4px 0; padding: 15px; border-radius: 15px; background: rgba(255,255,255,0.025);
        border: 1px solid rgba(255,255,255,0.05); color: #81948a; font-size: 11px; line-height: 1.9; text-align: right; direction: rtl;
    }

    .stButton > button {
        min-height: 42px; border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.055) !important;
        background: rgba(255,255,255,0.025) !important; color: #b8c8bf !important;
        font-weight: 500 !important; transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: rgba(22,165,96,0.09) !important; border-color: rgba(22,165,96,0.22) !important;
        color: #ffffff !important; transform: translateY(-1px);
    }
    .new-chat button {
        background: linear-gradient(135deg, #16a562, #087440) !important; color: #ffffff !important;
        border: none !important; font-weight: 700 !important; box-shadow: 0 8px 24px rgba(17,160,92,0.16);
    }

    .topbar { display: flex; align-items: center; justify-content: space-between; padding: 4px 2px 20px; direction: rtl; }
    .profile { display: flex; align-items: center; gap: 12px; direction: ltr; }
    .profile-avatar {
        width: 46px; height: 46px; min-width: 46px; border-radius: 15px; display: flex; align-items: center; justify-content: center;
        background: linear-gradient(145deg, #1ab36c, #087440); font-size: 24px; box-shadow: 0 8px 25px rgba(0,0,0,0.28);
    }
    .profile-name { color: #ffffff; font-size: 18px; font-weight: 800; line-height: 1.1; text-align: right; }
    .profile-role { color: #71867b; font-size: 10px; margin-top: 4px; text-align: right; }
    .status {
        display: flex; align-items: center; gap: 7px; padding: 6px 11px; border-radius: 999px;
        background: rgba(23,168,101,0.07); border: 1px solid rgba(23,168,101,0.14); color: #6bd39c; font-size: 10px; font-weight: 600;
    }
    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #31d47e; box-shadow: 0 0 8px rgba(49,212,126,0.65); }

    .welcome { text-align: center; direction: rtl; padding: 42px 15px 28px; }
    .welcome-icon {
        width: 76px; height: 76px; margin: auto; display: flex; align-items: center; justify-content: center;
        border-radius: 24px; background: radial-gradient(circle at 35% 25%, #2bc77b, #087440); font-size: 36px;
        box-shadow: 0 18px 45px rgba(0,0,0,0.35), 0 0 45px rgba(23,168,101,0.08);
    }
    .welcome h1 { color: #ffffff; font-size: 30px; font-weight: 800; margin: 19px 0 7px; }
    .welcome p { max-width: 560px; margin: auto; color: #84988d; font-size: 13px; line-height: 2; }
    .quick-heading { color: #667b70; font-size: 10px; font-weight: 700; text-align: right; direction: rtl; margin: 20px 2px 9px; }

    .chat-area { direction: rtl; margin-top: 8px; }
    .message-row { display: flex; width: 100%; margin: 18px 0; direction: rtl; }
    .message-row.user { justify-content: flex-start; }
    .message-row.assistant { justify-content: flex-end; }
    .message-container { display: flex; align-items: flex-end; gap: 9px; max-width: 78%; }
    .message-row.user .message-container { flex-direction: row-reverse; }
    .message-row.assistant .message-container { flex-direction: row; }
    
    .avatar {
        width: 34px; height: 34px; min-width: 34px; border-radius: 11px; display: flex; align-items: center; justify-content: center; font-size: 16px;
    }
    .avatar.user { background: #17251e; border: 1px solid rgba(255,255,255,0.055); }
    .avatar.assistant { background: linear-gradient(145deg, #18a967, #087440); box-shadow: 0 5px 17px rgba(20,160,92,0.13); }
    
    .message-bubble { padding: 11px 15px; font-size: 13px; line-height: 1.95; direction: rtl; text-align: right; word-break: break-word; }
    .message-row.user .message-bubble {
        background: #112019; border: 1px solid rgba(255,255,255,0.045); color: #dce8e1; border-radius: 17px 5px 17px 17px;
    }
    .message-row.assistant .message-bubble {
        background: linear-gradient(145deg, rgba(16,38,27,0.96), rgba(9,25,18,0.96));
        border: 1px solid rgba(23,168,101,0.12); color: #e3ede7; border-radius: 5px 17px 17px 17px;
    }

    .thinking { display: flex; align-items: center; gap: 8px; direction: rtl; color: #71867b; font-size: 11px; padding: 9px 4px; }
    .thinking-dot { width: 6px; height: 6px; border-radius: 50%; background: #25c777; animation: pulse 1.1s infinite ease-in-out; }
    @keyframes pulse { 0%, 100% { opacity: .25; transform: scale(.8); } 50% { opacity: 1; transform: scale(1); } }

    div[data-testid="stChatInput"] { direction: rtl; }
    div[data-testid="stChatInput"] textarea {
        background: #0b1811 !important; border: 1px solid rgba(255,255,255,0.075) !important; color: #eef5f0 !important;
        border-radius: 18px !important; font-size: 13px !important; padding: 14px 17px !important; box-shadow: 0 10px 35px rgba(0,0,0,0.18);
    }
    div[data-testid="stChatInput"] textarea:focus {
        border-color: rgba(24,169,103,0.42) !important; box-shadow: 0 0 0 1px rgba(24,169,103,0.12), 0 10px 35px rgba(0,0,0,0.18) !important;
    }

    .app-footer { text-align: center; direction: rtl; color: #3f5148; font-size: 9px; margin-top: 30px; padding-bottom: 8px; }

    @media (max-width: 768px) {
        .block-container { padding: 0.8rem 10px 6rem; }
        .message-container { max-width: 91%; }
        .welcome { padding-top: 25px; }
        .welcome-icon { width: 68px; height: 68px; font-size: 31px; }
        .welcome h1 { font-size: 25px; }
        .status { display: none; }
        .profile-avatar { width: 42px; height: 42px; min-width: 42px; }
        .message-bubble { font-size: 12px; padding: 10px 13px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def render_message(role: str, content: str):
safe_message = html.escape(str(content)).replace("\n", "<br>")

if role == "user":
    avatar, avatar_class, row_class = "👤", "user", "user"
else:
    avatar, avatar_class, row_class = "👴", "assistant", "assistant"

st.markdown(
    f"""
    <div class="message-row {row_class}">
        <div class="message-container">
            <div class="avatar {avatar_class}">{avatar}</div>
            <div class="message-bubble">{safe_message}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

def render_sidebar():
with st.sidebar:
st.markdown(
"""
<div class="sidebar-brand">
<div class="sidebar-logo">⚽</div>
<div class="sidebar-brand-text">
<div class="sidebar-brand-title">TRIVIO</div>
<div class="sidebar-brand-subtitle">FOOTBALL AI AGENT</div>
</div>
</div>
""",
unsafe_allow_html=True,
)

    st.markdown('<div class="new-chat">', unsafe_allow_html=True)
    if st.button("＋  محادثة جديدة", use_container_width=True):
        reset_conversation()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">اسأل عم مجدي</div>', unsafe_allow_html=True)

    questions = [
        "مين بيلعب دلوقتي؟",
        "ماتش الأهلي الجاي إمتى؟",
        "آخر أخبار الزمالك إيه؟",
        "حللّي آخر ماتش لليفربول",
    ]

    for i, q in enumerate(questions):
        if st.button(q, key=f"sq_{i}", use_container_width=True):
            st.session_state.pending_question = q
            st.rerun()

    st.markdown(
        """
        <div class="sidebar-description">
            <strong>عم مجدي (v1.0)</strong><br>
            وكيل ذكاء اصطناعي (AI Agent) مبني لتحليل البيانات الكروية، الأخبار، والمباريات المباشرة بدقة عالية.
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_header():
st.markdown(
"""
<div class="topbar">
<div class="profile">
<div class="profile-avatar">👴</div>
<div class="profile-info">
<div class="profile-name">عم مجدي</div>
<div class="profile-role">قاعدلك على القهوة ⚽</div>
</div>
</div>
<div class="status"><span class="status-dot"></span> متصل بالسيرفر</div>
</div>
""",
unsafe_allow_html=True,
)

def render_welcome_dashboard():
st.markdown(
"""
<div class="welcome">
<div class="welcome-icon">⚽</div>
<h1>قولّي يا كابتن 👋</h1>
<p>أنا <span style="color: #43ce88; font-weight: 700;">عم مجدي</span>، قاعدلك أهو. عايز تعرف ماتش، نتيجة، خبر، ميعاد، ولا نفصص ماتش ونشوف حصل فيه إيه؟ قول بس وأنا معاك.</p>
</div>
<div class="quick-heading">أمثلة للأسئلة المتاحة</div>
""",
unsafe_allow_html=True,
)

prompts = [
    ("🔴", "مين بيلعب دلوقتي؟"),
    ("📅", "ماتش الأهلي الجاي إمتى؟"),
    ("📰", "آخر أخبار الزمالك إيه؟"),
    ("⚽", "حللّي آخر ماتش لليفربول"),
]

col1, col2 = st.columns(2, gap="small")
for i, (icon, text) in enumerate(prompts):
    with (col1 if i % 2 == 0 else col2):
        if st.button(f"{icon}  {text}", key=f"q_{i}", use_container_width=True):
            st.session_state.pending_question = text
            st.rerun()

def main():
initialize_session()
inject_custom_css()

render_sidebar()
render_header()

if not st.session_state.messages:
    render_welcome_dashboard()
else:
    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"])
    st.markdown("</div>", unsafe_allow_html=True)

user_input = st.chat_input("قول لعم مجدي عايز تعرف إيه...")
active_prompt = st.session_state.pending_question or user_input

if st.session_state.pending_question:
    st.session_state.pending_question = None

if active_prompt and active_prompt.strip():
    prompt_text = active_prompt.strip()
    
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    render_message("user", prompt_text)

    thinking_ui = st.empty()
    thinking_ui.markdown(
        """
        <div class="thinking">
            <div class="thinking-dot"></div>
            <span>عم مجدي بيفكر في خطة اللعب...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        response_text = ask_backend(st.session_state.session_id, prompt_text)
        
        thinking_ui.empty()
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        render_message("assistant", response_text)

    except requests.exceptions.ConnectionError:
        thinking_ui.empty()
        error_msg = "يا نجم، مش قادر أوصل للسيرفر دلوقتي. اتأكد إن الـ API شغال وجرب تاني."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        render_message("assistant", error_msg)
        logger.error("Connection Error to Backend.")
        
    except requests.exceptions.Timeout:
        thinking_ui.empty()
        error_msg = "بص يا كابتن، السيرفر خد وقت أطول من اللازم. الشبكة تقيلة شوية، جرب تسألني تاني."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        render_message("assistant", error_msg)
        logger.error("Timeout Error to Backend.")
        
    except Exception as e:
        thinking_ui.empty()
        error_msg = "حصلت مشكلة تقنية وأنا بكلم السيستم. جرب سؤال تاني يا نجم."
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        render_message("assistant", error_msg)
        logger.exception(f"Unexpected Backend Error: {e}")

st.markdown(
    '<div class="app-footer">Trivio Architecture · Powered by Multi-Agent AI · Engineered for Scale</div>',
    unsafe_allow_html=True
)

if name == "main":
