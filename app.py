import os
import html
import logging
import uuid
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ============================================================
# Configuration
# ============================================================

APP_NAME = "TRIVIO"
AGENT_NAME = "عم مجدي"

API_TIMEOUT = 90
MAX_RETRIES = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("trivio-ui")


st.set_page_config(
    page_title="Trivio | عم مجدي",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# App helpers
# ============================================================

def get_chat_endpoint() -> str:
    """Read the backend URL from Streamlit secrets or environment."""
    try:
        endpoint = st.secrets.get("CHAT_ENDPOINT")
        if endpoint:
            return str(endpoint).strip()
    except Exception:
        pass

    return os.getenv("CHAT_ENDPOINT", "").strip()


CHAT_ENDPOINT = get_chat_endpoint()


@st.cache_resource(show_spinner=False)
def get_api_session() -> requests.Session:
    """Create one reusable HTTP session with sensible retries."""
    session = requests.Session()

    retry_strategy = Retry(
        total=MAX_RETRIES,
        connect=MAX_RETRIES,
        read=MAX_RETRIES,
        status=MAX_RETRIES,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        raise_on_status=False,
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10,
    )

    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Trivio-Magdy-Streamlit/2.0",
        }
    )

    return session


def ask_backend(session_id: str, message: str) -> str:
    """Send a message to the FastAPI agent and return its answer."""
    payload = {
        "id": session_id,
        "message": message,
    }

    logger.info(
        "Sending request to Magdy API | session=%s",
        session_id[:8],
    )

    response = get_api_session().post(
        CHAT_ENDPOINT,
        json=payload,
        timeout=(10, API_TIMEOUT),
    )

    response.raise_for_status()

    try:
        data: Any = response.json()
    except ValueError as exc:
        raise ValueError("Backend returned invalid JSON.") from exc

    if isinstance(data, dict):
        message_value = data.get("message")

        if message_value is None:
            raise ValueError("Backend response does not contain 'message'.")

        return str(message_value).strip()

    if isinstance(data, str):
        return data.strip()

    raise ValueError("Unexpected backend response format.")


def initialize_state() -> None:
    """Initialize all session-state values once."""
    defaults = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "pending_question": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_conversation() -> None:
    """Start a completely fresh agent conversation."""
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pending_question = None
    st.toast("بدأنا محادثة جديدة ⚽", icon="🔄")


def queue_question(question: str) -> None:
    """Queue a suggested question for the main chat loop."""
    st.session_state.pending_question = question
    st.rerun()


# ============================================================
# Styling
# ============================================================

def inject_css() -> None:
    """Modern dark football-themed UI with Arabic RTL support."""
    st.markdown(
        """
        <style>
        @import url(
            'https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap'
        );

        :root {
            --bg: #06100b;
            --surface: #0b1811;
            --surface-2: #0f2017;
            --surface-3: #13281c;
            --border: rgba(255, 255, 255, 0.07);
            --border-green: rgba(35, 203, 121, 0.22);
            --text: #edf7f1;
            --muted: #82978b;
            --muted-2: #5d7065;
            --green: #20c778;
            --green-dark: #087542;
            --shadow: 0 20px 55px rgba(0, 0, 0, 0.28);
        }

        * {
            box-sizing: border-box;
        }

        html,
        body,
        [class*="css"] {
            font-family: "Cairo", sans-serif !important;
        }

        body {
            background: var(--bg);
        }

        .stApp {
            min-height: 100vh;
            color: var(--text);
            background:
                radial-gradient(
                    circle at 50% -10%,
                    rgba(32, 199, 120, 0.14),
                    transparent 34%
                ),
                radial-gradient(
                    circle at 0% 100%,
                    rgba(15, 111, 65, 0.08),
                    transparent 28%
                ),
                var(--bg);
        }

        #MainMenu,
        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            width: 100%;
            max-width: 1120px;
            padding-top: 1.25rem;
            padding-bottom: 7rem;
        }

        /* ---------------- Sidebar ---------------- */

        [data-testid="stSidebar"] {
            background:
                linear-gradient(
                    180deg,
                    #09170f 0%,
                    #06100b 100%
                );
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.2rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            direction: ltr;
            padding: 4px 8px 22px;
        }

        .brand-logo {
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 15px;
            background:
                radial-gradient(
                    circle at 30% 20%,
                    #39dc8b,
                    #0a7947 70%
                );
            box-shadow:
                0 12px 30px rgba(23, 185, 108, 0.20);
            font-size: 22px;
        }

        .brand-title {
            color: #ffffff;
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.3px;
            line-height: 1.05;
        }

        .brand-subtitle {
            margin-top: 5px;
            color: #667b6f;
            font-size: 9px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        .sidebar-section-title {
            margin: 22px 8px 9px;
            color: #61766a;
            direction: rtl;
            text-align: right;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        .sidebar-info {
            margin: 18px 4px 0;
            padding: 15px;
            border: 1px solid var(--border);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.025);
            color: #81958a;
            direction: rtl;
            text-align: right;
            font-size: 11px;
            line-height: 1.9;
        }

        .sidebar-info strong {
            color: #d8e9df;
        }

        /* ---------------- Buttons ---------------- */

        .stButton > button {
            min-height: 42px;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.025) !important;
            color: #b8c9c0 !important;
            font-family: "Cairo", sans-serif !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            transition:
                transform 0.18s ease,
                background 0.18s ease,
                border-color 0.18s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: var(--border-green) !important;
            background: rgba(32, 199, 120, 0.08) !important;
            color: #ffffff !important;
        }

        .primary-button .stButton > button {
            border: 0 !important;
            color: #ffffff !important;
            background:
                linear-gradient(
                    135deg,
                    #1ebc72 0%,
                    #087542 100%
                ) !important;
            box-shadow:
                0 10px 25px rgba(21, 169, 96, 0.18);
        }

        /* ---------------- Header ---------------- */

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
            direction: rtl;
            margin-bottom: 8px;
        }

        .agent-profile {
            display: flex;
            align-items: center;
            gap: 12px;
            direction: ltr;
        }

        .agent-avatar {
            width: 48px;
            height: 48px;
            flex: 0 0 48px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 15px;
            background:
                linear-gradient(145deg, #1fc577, #087542);
            box-shadow:
                0 10px 28px rgba(0, 0, 0, 0.25);
            font-size: 23px;
        }

        .agent-name {
            color: #ffffff;
            direction: rtl;
            text-align: right;
            font-size: 17px;
            font-weight: 800;
            line-height: 1.1;
        }

        .agent-role {
            margin-top: 4px;
            color: var(--muted);
            direction: rtl;
            text-align: right;
            font-size: 10px;
        }

        .online-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            border: 1px solid rgba(32, 199, 120, 0.16);
            border-radius: 999px;
            background: rgba(32, 199, 120, 0.06);
            color: #70d99f;
            font-size: 10px;
            font-weight: 600;
            direction: rtl;
        }

        .online-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #2bd77e;
            box-shadow: 0 0 10px rgba(43, 215, 126, 0.7);
        }

        /* ---------------- Welcome ---------------- */

        .hero {
            max-width: 780px;
            margin: 0 auto;
            padding: 55px 12px 25px;
            direction: rtl;
            text-align: center;
        }

        .hero-icon {
            width: 82px;
            height: 82px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 25px;
            background:
                radial-gradient(
                    circle at 30% 20%,
                    #36d987,
                    #087542 72%
                );
            box-shadow:
                0 20px 50px rgba(0, 0, 0, 0.32),
                0 0 55px rgba(31, 196, 116, 0.08);
            font-size: 38px;
        }

        .hero h1 {
            margin: 0;
            color: #ffffff;
            font-size: clamp(27px, 4vw, 35px);
            font-weight: 800;
            letter-spacing: -0.4px;
        }

        .hero p {
            max-width: 650px;
            margin: 10px auto 0;
            color: #81958a;
            font-size: 13px;
            line-height: 2;
        }

        .hero-highlight {
            color: #43d88c;
            font-weight: 800;
        }

        .quick-title {
            margin: 12px 2px 9px;
            color: #61766a;
            direction: rtl;
            text-align: right;
            font-size: 10px;
            font-weight: 700;
        }

        /* ---------------- Chat ---------------- */

        .chat-shell {
            margin-top: 14px;
            direction: rtl;
        }

        [data-testid="stChatMessage"] {
            border: 1px solid var(--border);
            border-radius: 18px;
            background: rgba(10, 25, 17, 0.62);
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.10);
        }

        [data-testid="stChatMessage"]:has(
            [data-testid="chatAvatarIcon-user"]
        ) {
            background: rgba(17, 32, 25, 0.72);
        }

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li {
            direction: rtl;
            text-align: right;
            color: #e3eee8;
            font-size: 13px;
            line-height: 2;
        }

        [data-testid="stChatMessage"] ul,
        [data-testid="stChatMessage"] ol {
            direction: rtl;
            text-align: right;
        }

        /* ---------------- Chat input ---------------- */

        div[data-testid="stChatInput"] {
            direction: rtl;
        }

        div[data-testid="stChatInput"] textarea {
            min-height: 56px !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 18px !important;
            background: rgba(10, 24, 16, 0.96) !important;
            color: #f0f8f3 !important;
            font-family: "Cairo", sans-serif !important;
            font-size: 13px !important;
            line-height: 1.7 !important;
            box-shadow: var(--shadow);
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #607469 !important;
        }

        div[data-testid="stChatInput"] textarea:focus {
            border-color: rgba(32, 199, 120, 0.42) !important;
            box-shadow:
                0 0 0 1px rgba(32, 199, 120, 0.12),
                var(--shadow) !important;
        }

        /* ---------------- Thinking ---------------- */

        .thinking {
            display: flex;
            align-items: center;
            gap: 9px;
            width: fit-content;
            margin: 10px 0;
            padding: 9px 13px;
            border: 1px solid var(--border);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.025);
            color: #7d9286;
            direction: rtl;
            font-size: 10px;
        }

        .thinking-dots {
            display: inline-flex;
            gap: 4px;
        }

        .thinking-dots span {
            width: 5px;
            height: 5px;
            border-radius: 50%;
            background: #2bd77e;
            animation: pulse 1.1s infinite ease-in-out;
        }

        .thinking-dots span:nth-child(2) {
            animation-delay: 0.15s;
        }

        .thinking-dots span:nth-child(3) {
            animation-delay: 0.3s;
        }

        @keyframes pulse {
            0%,
            100% {
                opacity: 0.25;
                transform: translateY(0);
            }

            50% {
                opacity: 1;
                transform: translateY(-2px);
            }
        }

        /* ---------------- Footer ---------------- */

        .footer {
            margin-top: 35px;
            padding: 10px;
            color: #3e5147;
            direction: rtl;
            text-align: center;
            font-size: 9px;
        }

        /* ---------------- Mobile ---------------- */

        @media (max-width: 768px) {
            .block-container {
                padding: 0.8rem 10px 6rem;
            }

            .online-pill {
                display: none;
            }

            .agent-avatar {
                width: 43px;
                height: 43px;
                flex-basis: 43px;
            }

            .agent-name {
                font-size: 15px;
            }

            .hero {
                padding-top: 32px;
            }

            .hero-icon {
                width: 70px;
                height: 70px;
                border-radius: 21px;
                font-size: 31px;
            }

            .hero p {
                font-size: 12px;
            }

            [data-testid="stChatMessage"] {
                border-radius: 15px;
            }

            [data-testid="stChatMessage"] p,
            [data-testid="stChatMessage"] li {
                font-size: 12px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UI components
# ============================================================

QUICK_QUESTIONS: List[str] = [
    "مين بيلعب دلوقتي؟",
    "ماتش الأهلي الجاي إمتى؟",
    "آخر أخبار الزمالك إيه؟",
    "حللّي آخر ماتش لليفربول",
]


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-logo">⚽</div>
                <div>
                    <div class="brand-title">TRIVIO</div>
                    <div class="brand-subtitle">FOOTBALL AI AGENT</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="primary-button">', unsafe_allow_html=True)
        if st.button(
            "＋  محادثة جديدة",
            use_container_width=True,
            key="new_chat",
        ):
            reset_conversation()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="sidebar-section-title">اسأل عم مجدي</div>',
            unsafe_allow_html=True,
        )

        for index, question in enumerate(QUICK_QUESTIONS):
            if st.button(
                question,
                use_container_width=True,
                key=f"sidebar_question_{index}",
            ):
                queue_question(question)

        st.markdown(
            """
            <div class="sidebar-info">
                <strong>عم مجدي</strong><br>
                صاحبك اللي بيحب الكورة وبيتابعها من زمان.
                اسأله عن المواعيد، النتائج، المباريات المباشرة،
                الأخبار أو تحليل الماتشات.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="sidebar-info">
                <strong>💡 نصيحة</strong><br>
                كل ما كان سؤالك محدد أكتر، عم مجدي يقدر
                يساعدك بإجابة أدق.
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_header() -> None:
    st.markdown(
        """
        <div class="topbar">
            <div class="agent-profile">
                <div class="agent-avatar">👴</div>
                <div>
                    <div class="agent-name">عم مجدي</div>
                    <div class="agent-role">
                        قاعدلك على القهوة · Football AI
                    </div>
                </div>
            </div>

            
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-icon">⚽</div>
            <h1>قولّي يا كابتن 👋</h1>
            <p>
                أنا <span class="hero-highlight">عم مجدي</span>،
                صاحبك اللي فاهم الكورة من زمان.
                عايز تعرف ماتش، نتيجة، ميعاد، خبر،
                أو نفصص ماتش ونشوف حصل فيه إيه؟
                <br>
                <strong>قول بس وأنا معاك.</strong>
            </p>
        </section>

        <div class="quick-title">أمثلة تقدر تبدأ بيها</div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2, gap="small")

    for index, question in enumerate(QUICK_QUESTIONS):
        column = col1 if index % 2 == 0 else col2

        with column:
            if st.button(
                question,
                use_container_width=True,
                key=f"hero_question_{index}",
            ):
                queue_question(question)


def render_chat() -> None:
    """Render conversation using Streamlit's native chat components."""
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        role = message["role"]
        avatar = "👤" if role == "user" else "👴"

        with st.chat_message(role, avatar=avatar):
            st.markdown(message["content"])

    st.markdown("</div>", unsafe_allow_html=True)


def render_thinking() -> Any:
    placeholder = st.empty()

    placeholder.markdown(
        """
        <div class="thinking">
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            عم مجدي بيفكر في الموضوع...
        </div>
        """,
        unsafe_allow_html=True,
    )

    return placeholder


# ============================================================
# Message handling
# ============================================================

def get_error_message(error: Exception) -> str:
    """Convert technical exceptions into friendly Arabic messages."""
    if isinstance(error, requests.exceptions.Timeout):
        return (
            "بص يا كابتن، السيرفر اتأخر شوية في الرد. "
            "جرّب السؤال تاني بعد لحظة."
        )

    if isinstance(error, requests.exceptions.ConnectionError):
        return (
            "يا نجم، مش قادر أوصل للسيرفر دلوقتي. "
            "اتأكد إن الـ API شغال وجرب تاني."
        )

    if isinstance(error, requests.exceptions.HTTPError):
        status_code = getattr(
            getattr(error, "response", None),
            "status_code",
            None,
        )

        if status_code == 429:
            return (
                "الطلبات كتير على السيرفر دلوقتي. "
                "استنى لحظة وجرب تاني."
            )

        if status_code and status_code >= 500:
            return (
                "السيرفر نفسه واجه مشكلة مؤقتة. "
                "جرّب تاني بعد شوية يا كابتن."
            )

        return (
            "حصلت مشكلة أثناء الاتصال بالخدمة. "
            "جرّب السؤال تاني."
        )

    return (
        "حصلت مشكلة تقنية وأنا بكلم السيستم. "
        "جرّب السؤال تاني يا نجم."
    )


def process_message(prompt: str) -> None:
    """Append the user message, call the agent, and render the response."""
    prompt = prompt.strip()

    if not prompt:
        return

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    thinking = render_thinking()

    try:
        response_text = ask_backend(
            st.session_state.session_id,
            prompt,
        )

        if not response_text:
            response_text = (
                "مش لاقي رد مناسب دلوقتي يا كابتن. "
                "جرّب تسألني بطريقة تانية."
            )

    except Exception as exc:
        logger.exception("Backend request failed")
        response_text = get_error_message(exc)

    finally:
        thinking.empty()

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response_text,
        }
    )

    with st.chat_message("assistant", avatar="👴"):
        st.markdown(response_text)


# ============================================================
# Main
# ============================================================

def main() -> None:
    initialize_state()
    inject_css()
    render_sidebar()
    render_header()

    if st.session_state.messages:
        render_chat()
    else:
        render_welcome()

    user_input = st.chat_input(
        "قول لعم مجدي عايز تعرف إيه... ⚽"
    )

    pending_question = st.session_state.pending_question

    if pending_question:
        st.session_state.pending_question = None

    active_prompt = pending_question or user_input

    if active_prompt:
        process_message(active_prompt)

    st.markdown(
        """
        <div class="footer">
            Trivio · عم مجدي · Egyptian Football AI
            <br>
            Built with FastAPI + LangGraph
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
