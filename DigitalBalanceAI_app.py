import streamlit as st
import sqlite3
import hashlib
import json
import math
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

DB_FILE = "digitalbalance.db"

st.set_page_config(
    page_title="DigitalBalance AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme + global styling
# -----------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

dark = st.session_state.theme == "Dark"

BG = "#0b1220" if dark else "#f6f8fc"
CARD = "#111b2e" if dark else "#ffffff"
TEXT = "#eef4ff" if dark else "#182230"
MUTED = "#a9b5c7" if dark else "#667085"
BORDER = "#263650" if dark else "#e6eaf0"
ACCENT = "#6c63ff"
ACCENT2 = "#00b8a9"
WARNING = "#f59e0b"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{
        font-family: 'Poppins', sans-serif;
    }}
    .stApp {{
        background: {BG};
        color: {TEXT};
    }}
    .block-container {{
        max-width: 1250px;
        padding-top: 1.2rem;
        padding-bottom: 4rem;
    }}
    section[data-testid="stSidebar"] {{
        background: {CARD};
        border-right: 1px solid {BORDER};
    }}
    .hero {{
        padding: 28px;
        border-radius: 24px;
        background: linear-gradient(135deg, #6c63ff 0%, #8b5cf6 48%, #00b8a9 100%);
        color: white;
        box-shadow: 0 14px 40px rgba(70,60,160,.18);
        margin-bottom: 22px;
    }}
    .hero h1 {{
        font-size: 2.15rem;
        margin: 0 0 5px 0;
        font-weight: 800;
    }}
    .hero p {{
        margin: 0;
        opacity: .94;
        font-size: 1rem;
    }}
    .card {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 26px rgba(0,0,0,.05);
    }}
    .metric {{
        background: {CARD};
        border: 1px solid {BORDER};
        border-radius: 18px;
        padding: 18px;
        text-align: center;
        min-height: 120px;
    }}
    .metric .value {{
        font-size: 2rem;
        font-weight: 800;
        color: {ACCENT};
    }}
    .metric .label {{
        color: {MUTED};
        font-size: .86rem;
    }}
    .pill {{
        display: inline-block;
        padding: 6px 12px;
        border-radius: 999px;
        background: rgba(108,99,255,.12);
        color: {ACCENT};
        font-size: .78rem;
        font-weight: 700;
        margin: 3px;
    }}
    .insight {{
        padding: 14px 16px;
        border-left: 4px solid {ACCENT};
        background: rgba(108,99,255,.07);
        border-radius: 12px;
        margin: 8px 0;
    }}
    .small {{
        color: {MUTED};
        font-size: .86rem;
    }}
    .section-title {{
        font-size: 1.35rem;
        font-weight: 800;
        margin: 10px 0 12px;
    }}
    div.stButton > button {{
        border-radius: 12px;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Database
# -----------------------------
def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS assessments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            goals TEXT NOT NULL,
            answers TEXT NOT NULL,
            score REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(username, password):
    con = db()
    try:
        con.execute(
            "INSERT INTO users(username,password,created_at) VALUES(?,?,?)",
            (username.strip(), hash_password(password), datetime.now().isoformat(timespec="seconds"))
        )
        con.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        con.close()

def check_login(username, password):
    con = db()
    row = con.execute(
        "SELECT username FROM users WHERE username=? AND password=?",
        (username.strip(), hash_password(password))
    ).fetchone()
    con.close()
    return row is not None

def save_assessment(username, goals, answers, score):
    con = db()
    con.execute(
        "INSERT INTO assessments(username,created_at,goals,answers,score) VALUES(?,?,?,?,?)",
        (username, datetime.now().isoformat(timespec="seconds"),
         json.dumps(goals), json.dumps(answers), float(score))
    )
    con.commit()
    con.close()

def get_history(username):
    con = db()
    rows = con.execute(
        "SELECT id,created_at,goals,answers,score FROM assessments "
        "WHERE username=? ORDER BY created_at ASC", (username,)
    ).fetchall()
    con.close()
    data = []
    for r in rows:
        data.append({
            "id": r[0],
            "date": r[1],
            "goals": json.loads(r[2]),
            "answers": json.loads(r[3]),
            "score": float(r[4]),
        })
    return data

def save_chat(username, role, message):
    con = db()
    con.execute(
        "INSERT INTO chats(username,created_at,role,message) VALUES(?,?,?,?)",
        (username, datetime.now().isoformat(timespec="seconds"), role, message)
    )
    con.commit()
    con.close()

def get_chats(username):
    con = db()
    rows = con.execute(
        "SELECT role,message FROM chats WHERE username=? ORDER BY id",
        (username,)
    ).fetchall()
    con.close()
    return rows

# -----------------------------
# Questions + scoring model
# -----------------------------
GOALS = {
    "📱 Screen Time": "Understand overall daily screen exposure.",
    "⚖️ Digital Balance": "Understand whether digital use feels balanced.",
    "📚 Study & Screen": "Understand study-related digital habits.",
    "🌙 Night Usage": "Understand late-night device habits.",
    "🔔 Distraction Analyzer": "Understand notifications and checking behaviour.",
}

QUESTION_BANK = {
    "📱 Screen Time": [
        ("On a typical day, how long do you use screens outside essential work/study?",
         ["Less than 1 hour", "1–2 hours", "2–4 hours", "4–6 hours", "More than 6 hours"]),
        ("How often do you continue using a device longer than planned?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you check your phone without a specific reason?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How difficult is it to stop using your phone when you decide to?",
         ["Very easy", "Easy", "Sometimes difficult", "Difficult", "Very difficult"]),
    ],
    "⚖️ Digital Balance": [
        ("How balanced does your digital life feel right now?",
         ["Very balanced", "Mostly balanced", "Mixed", "Somewhat unbalanced", "Very unbalanced"]),
        ("How often does digital entertainment replace an offline activity you planned?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you intentionally take screen-free breaks?",
         ["Very often", "Often", "Sometimes", "Rarely", "Never"]),
        ("How satisfied are you with the way technology fits into your day?",
         ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"]),
    ],
    "📚 Study & Screen": [
        ("How often do notifications interrupt your study?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you switch from study to entertainment/social media?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you use your device for focused learning?",
         ["Very often", "Often", "Sometimes", "Rarely", "Never"]),
        ("How easy is it to stay focused during a digital study session?",
         ["Very easy", "Easy", "Mixed", "Difficult", "Very difficult"]),
    ],
    "🌙 Night Usage": [
        ("How often do you use a phone or other screen close to bedtime?",
         ["Never", "Rarely", "Sometimes", "Often", "Every night"]),
        ("How often do you keep scrolling after deciding to sleep?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you check your phone if you wake during the night?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How consistent is your screen-free wind-down routine?",
         ["Very consistent", "Usually", "Sometimes", "Rarely", "Not at all"]),
    ],
    "🔔 Distraction Analyzer": [
        ("How often do you check notifications immediately?",
         ["Never", "Rarely", "Sometimes", "Often", "Always"]),
        ("How often do you unlock your phone automatically out of habit?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do short checks become longer sessions?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
        ("How often do you feel pulled back to an app after closing it?",
         ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
    ],
}

RISK = {
    "Never": 0, "Very balanced": 0, "Very satisfied": 0, "Very often": 0,
    "Very consistent": 0, "Very easy": 0, "Less than 1 hour": 0,
    "1–2 hours": 1, "Rarely": 1, "Balanced": 1, "Satisfied": 1, "Easy": 1,
    "Usually": 1,
    "2–4 hours": 2, "Sometimes": 2, "Mixed": 2, "Neutral": 2,
    "Sometimes difficult": 2,
    "4–6 hours": 3, "Often": 3, "Somewhat unbalanced": 3, "Dissatisfied": 3,
    "Difficult": 3,
    "More than 6 hours": 4, "Very often": 4, "Very unbalanced": 4,
    "Very dissatisfied": 4, "Very difficult": 4, "Every night": 4,
    "Not at all": 4, "Always": 4,
}

def answer_risk(answer):
    return RISK.get(answer, 2)

def score_from_answers(answers):
    if not answers:
        return 0
    avg = np.mean([answer_risk(a) for a in answers])
    return round(max(0, min(100, 100 - (avg / 4) * 100)), 1)

def goal_scores(goals, answers):
    result = {}
    for goal in goals:
        vals = [answer_risk(a) for g, _, a in answers if g == goal]
        result[goal] = round(max(0, min(100, 100 - (np.mean(vals)/4)*100)), 1) if vals else 0
    return result

def score_label(score):
    if score >= 80:
        return "Strong digital balance"
    if score >= 60:
        return "Mostly balanced"
    if score >= 40:
        return "Needs attention"
    return "High-priority habits"

def behaviour_twin(scores):
    vals = {
        "Focus": scores.get("📚 Study & Screen", 50),
        "Distraction Control": scores.get("🔔 Distraction Analyzer", 50),
        "Night Balance": scores.get("🌙 Night Usage", 50),
        "Screen Balance": scores.get("⚖️ Digital Balance", 50),
        "Screen Time": scores.get("📱 Screen Time", 50),
    }
    return vals

def explain_factors(answer_rows):
    ranked = sorted(
        [(g, q, a, answer_risk(a)) for g, q, a in answer_rows],
        key=lambda x: x[3],
        reverse=True
    )
    return ranked[:3]

def action_plan(scores):
    actions = []
    if scores.get("📱 Screen Time", 100) < 65:
        actions.append("Set one realistic screen-free block each day.")
    if scores.get("🔔 Distraction Analyzer", 100) < 65:
        actions.append("Turn off non-essential notifications during focus periods.")
    if scores.get("🌙 Night Usage", 100) < 65:
        actions.append("Create a short screen-free wind-down before sleep.")
    if scores.get("📚 Study & Screen", 100) < 65:
        actions.append("Use focused study sessions with entertainment apps closed.")
    if scores.get("⚖️ Digital Balance", 100) < 65:
        actions.append("Plan one offline activity alongside your digital routine.")
    if not actions:
        actions = [
            "Keep your current routine and review it weekly.",
            "Protect your screen-free breaks.",
            "Reassess your habits after a few days."
        ]
    return actions[:3]

def habit_connections(answers):
    text = " ".join(answers).lower()
    connections = []
    if any(x in text for x in ["often", "very often", "always", "every night"]):
        connections.append(("Frequent checking", "may reinforce", "notification-driven phone use"))
    if "more than 6 hours" in text or "4–6 hours" in text:
        connections.append(("Long screen exposure", "can coexist with", "fewer intentional breaks"))
    if "very difficult" in text or "difficult" in text:
        connections.append(("Stopping feels difficult", "may be linked with", "longer unplanned sessions"))
    if "often" in text and "study" in text:
        connections.append(("Study interruptions", "can affect", "focus during digital learning"))
    if not connections:
        connections.append(("Your reported habits", "are being explored as", "patterns rather than diagnoses"))
    return connections[:4]

def make_report(username, score, scores, goals, factors, actions):
    lines = [
        "DIGITALBALANCE AI — PERSONAL DIGITAL WELLNESS REPORT",
        "=" * 55,
        f"User: {username}",
        f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}",
        "",
        f"Overall digital-balance indicator: {score}/100",
        f"Interpretation: {score_label(score)}",
        "",
        "GOAL INDICATORS",
    ]
    for g, s in scores.items():
        lines.append(f"- {g}: {s}/100")
    lines += ["", "TOP EXPLAINABLE FACTORS"]
    for g, q, a, r in factors:
        lines.append(f"- {g}: {q} | Response: {a}")
    lines += ["", "PERSONALISED ACTION PLAN"]
    for a in actions:
        lines.append(f"- {a}")
    lines += [
        "",
        "PRIVACY & AI NOTE",
        "This report is based on user-provided responses. It is not a medical diagnosis.",
        "DigitalBalance AI does not secretly monitor the device.",
    ]
    return "\n".join(lines)

# -----------------------------
# Session state
# -----------------------------
defaults = {
    "logged_in": False,
    "username": "",
    "page": "Dashboard",
    "selected_goals": list(GOALS.keys()),
    "answers": [],
    "last_score": None,
    "last_goal_scores": {},
    "last_factors": [],
    "last_actions": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -----------------------------
# Auth
# -----------------------------
if not st.session_state.logged_in:
    st.markdown("""
    <div class="hero">
      <h1>⚖️ DigitalBalance AI</h1>
      <p>Understand your digital life. Balance it better.</p>
    </div>
    """, unsafe_allow_html=True)

    a, b = st.columns(2)
    with a:
        st.markdown("### 🔐 Sign in")
        user = st.text_input("Username", key="login_user")
        pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Sign in", use_container_width=True):
            if check_login(user, pw):
                st.session_state.logged_in = True
                st.session_state.username = user.strip()
                st.rerun()
            else:
                st.error("Username or password is incorrect.")
    with b:
        st.markdown("### ✨ Create account")
        nu = st.text_input("New username", key="new_user")
        npw = st.text_input("New password", type="password", key="new_pw")
        cpw = st.text_input("Confirm password", type="password", key="confirm_pw")
        if st.button("Create account", use_container_width=True):
            if not nu.strip() or not npw:
                st.warning("Please enter a username and password.")
            elif npw != cpw:
                st.error("Passwords do not match.")
            elif create_user(nu, npw):
                st.success("Account created. You can now sign in.")
            else:
                st.error("That username already exists.")
    st.markdown(
        '<div class="small">Privacy-first demo: information is entered by the user; no secret device monitoring is used.</div>',
        unsafe_allow_html=True
    )
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## ⚖️ DigitalBalance AI")
    st.caption(f"Signed in as **{st.session_state.username}**")
    st.divider()

    pages = [
        "Dashboard", "Smart Questions", "Analysis", "Digital Behaviour Twin",
        "Habit Connection Map", "AI Coach", "Progress & Calendar",
        "What-If Lab", "Milestones", "Wellness Report", "Privacy & AI Ethics"
    ]
    current = st.session_state.page
    choice = st.radio("Navigate", pages, index=pages.index(current))
    st.session_state.page = choice

    st.divider()
    st.session_state.theme = st.selectbox(
        "Appearance", ["Light", "Dark"],
        index=0 if st.session_state.theme == "Light" else 1
    )
    if st.button("Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# -----------------------------
# Helpers for page charts
# -----------------------------
def plot_bar(labels, values, title, y_title="Score"):
    if not PLOTLY_OK:
        st.bar_chart(pd.DataFrame({"Score": values}, index=labels))
        return
    fig = go.Figure(go.Bar(x=labels, y=values))
    fig.update_layout(
        title=title, yaxis_title=y_title, yaxis_range=[0, 100],
        template="plotly_dark" if dark else "plotly_white",
        margin=dict(l=10, r=10, t=55, b=10),
        height=360
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_line(dates, scores, title):
    if not PLOTLY_OK:
        st.line_chart(pd.DataFrame({"Score": scores}, index=dates))
        return
    fig = go.Figure(go.Scatter(x=dates, y=scores, mode="lines+markers"))
    fig.update_layout(
        title=title, yaxis_title="Indicator", yaxis_range=[0, 100],
        template="plotly_dark" if dark else "plotly_white",
        margin=dict(l=10, r=10, t=55, b=10), height=350
    )
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Dashboard
# -----------------------------
if st.session_state.page == "Dashboard":
    st.markdown(
        f"""
        <div class="hero">
          <h1>Welcome back, {st.session_state.username} 👋</h1>
          <p>Understand your digital life. Balance it better.</p>
        </div>
        """, unsafe_allow_html=True
    )

    hist = get_history(st.session_state.username)
    latest = hist[-1] if hist else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric"><div class="value">{len(hist)}</div><div class="label">Assessments</div></div>', unsafe_allow_html=True)
    with c2:
        val = f"{latest['score']:.0f}" if latest else "—"
        st.markdown(f'<div class="metric"><div class="value">{val}</div><div class="label">Latest indicator</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric"><div class="value">{len(st.session_state.selected_goals)}</div><div class="label">Goals explored</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric"><div class="value">SDG 3</div><div class="label">Primary SDG</div></div>', unsafe_allow_html=True)

    st.markdown("### 🚀 Your DigitalBalance toolkit")
    cols = st.columns(5)
    items = [
        ("🧠", "Explain", "Understand why an indicator changed."),
        ("🧬", "Behaviour Twin", "See your five habit dimensions."),
        ("🕸️", "Connections", "Explore reported habit relationships."),
        ("🎯", "Action Plan", "Get three practical next steps."),
        ("↔️", "Compare", "Track change across assessments."),
    ]
    for col, (icon, title, desc) in zip(cols, items):
        with col:
            st.markdown(f'<div class="card"><h3>{icon} {title}</h3><div class="small">{desc}</div></div>', unsafe_allow_html=True)

    if latest:
        st.markdown("### 📊 Latest snapshot")
        latest_scores = goal_scores(latest["goals"], [
            (g, q, a) for g, qs in [(g, []) for g in latest["goals"]]
            for q, a in []
        ])
        # Rebuild goal scores from stored question rows where available.
        stored_answers = latest["answers"]
        if isinstance(stored_answers, list) and stored_answers and isinstance(stored_answers[0], list):
            rows = stored_answers
        else:
            rows = []
        if rows:
            gs = {}
            for g in latest["goals"]:
                vals = [answer_risk(x[2]) for x in rows if x[0] == g]
                gs[g] = round(100 - np.mean(vals)/4*100, 1) if vals else 0
            plot_bar(list(gs.keys()), list(gs.values()), "Latest goal indicators")
    else:
        st.info("Start your first Smart Questions assessment to unlock your dashboard.")

# -----------------------------
# Smart Questions
# -----------------------------
elif st.session_state.page == "Smart Questions":
    st.markdown('<div class="hero"><h1>🧠 Smart Questions</h1><p>A short self-reflection assessment powers your personalised analysis.</p></div>', unsafe_allow_html=True)

    selected = st.multiselect(
        "What would you like DigitalBalance AI to explore?",
        list(GOALS.keys()),
        default=st.session_state.selected_goals
    )
    if selected:
        st.session_state.selected_goals = selected
        total = sum(len(QUESTION_BANK[g]) for g in selected)
        st.caption(f"{total} questions • You can change your goals anytime.")

        with st.form("assessment_form"):
            rows = []
            for g in selected:
                st.markdown(f"### {g}")
                st.caption(GOALS[g])
                for idx, (q, options) in enumerate(QUESTION_BANK[g]):
                    ans = st.radio(q, options, key=f"{g}_{idx}")
                    rows.append((g, q, ans))
                st.divider()

            submitted = st.form_submit_button("✨ Analyse my digital balance", use_container_width=True)

        if submitted:
            answers_only = [x[2] for x in rows]
            score = score_from_answers(answers_only)
            gs = goal_scores(selected, rows)
            factors = explain_factors(rows)
            actions = action_plan(gs)

            st.session_state.answers = rows
            st.session_state.last_score = score
            st.session_state.last_goal_scores = gs
            st.session_state.last_factors = factors
            st.session_state.last_actions = actions

            save_assessment(st.session_state.username, selected, rows, score)
            st.success("Assessment saved. Your personalised analysis is ready.")
            st.session_state.page = "Analysis"
            st.rerun()
    else:
        st.warning("Select at least one goal.")

# -----------------------------
# Analysis
# -----------------------------
elif st.session_state.page == "Analysis":
    st.markdown('<div class="hero"><h1>📊 Your Digital Analysis</h1><p>From answers → patterns → explainable insights → actions.</p></div>', unsafe_allow_html=True)

    if st.session_state.last_score is None:
        hist = get_history(st.session_state.username)
        if hist:
            latest = hist[-1]
            st.session_state.last_score = latest["score"]
            st.session_state.selected_goals = latest["goals"]
        else:
            st.info("Complete Smart Questions first.")
            st.stop()

    score = st.session_state.last_score
    gs = st.session_state.last_goal_scores
    factors = st.session_state.last_factors
    actions = st.session_state.last_actions

    a, b, c = st.columns(3)
    with a:
        st.metric("Overall indicator", f"{score:.0f}/100")
    with b:
        st.metric("Interpretation", score_label(score))
    with c:
        st.metric("Goals explored", len(st.session_state.selected_goals))

    if gs:
        plot_bar(list(gs.keys()), list(gs.values()), "Digital Balance by goal")

    st.markdown("### 💡 Key insights")
    if score >= 80:
        st.markdown('<div class="insight">Your responses suggest a relatively intentional digital routine. The goal now is consistency.</div>', unsafe_allow_html=True)
    elif score >= 60:
        st.markdown('<div class="insight">Your responses show a mixed pattern. A few small habit changes could make your routine more intentional.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="insight">Several reported habits may deserve attention. Focus on one practical change at a time rather than changing everything together.</div>', unsafe_allow_html=True)

    st.markdown("### 🔍 Explainable AI — Why this result?")
    if factors:
        for g, q, atext, risk in factors:
            influence = "higher influence" if risk >= 3 else "moderate influence" if risk == 2 else "lower influence"
            st.markdown(
                f'<div class="card"><b>{g}</b><br>{q}<br><span class="small">Your response: {atext} · {influence} on this indicator.</span></div>',
                unsafe_allow_html=True
            )
    st.caption("The scoring model is transparent and heuristic; it is not a medical or psychological diagnosis.")

    st.markdown("### 🎯 Personalised Action Plan")
    for i, action in enumerate(actions, 1):
        st.markdown(f'<div class="insight"><b>{i}.</b> {action}</div>', unsafe_allow_html=True)

# -----------------------------
# Behaviour Twin
# -----------------------------
elif st.session_state.page == "Digital Behaviour Twin":
    st.markdown('<div class="hero"><h1>🧬 Digital Behaviour Twin</h1><p>A simplified visual profile built from your self-reported habits.</p></div>', unsafe_allow_html=True)

    scores = behaviour_twin(st.session_state.last_goal_scores)
    if PLOTLY_OK:
        categories = list(scores.keys())
        values = list(scores.values())
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=values, theta=categories, fill="toself", name="Your profile"))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            showlegend=False,
            template="plotly_dark" if dark else "plotly_white",
            height=500,
            margin=dict(l=20,r=20,t=40,b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.bar_chart(pd.DataFrame({"Indicator": scores}))

    st.markdown("### How to read it")
    st.markdown(
        '<div class="card">This is a project-level behaviour model. It does not diagnose health conditions or personality. '
        'Higher values mean stronger balance on the corresponding self-reported indicator.</div>',
        unsafe_allow_html=True
    )

# -----------------------------
# Habit Connection Map
# -----------------------------
elif st.session_state.page == "Habit Connection Map":
    st.markdown('<div class="hero"><h1>🕸️ Habit Connection Map</h1><p>Explore how reported digital habits may appear together.</p></div>', unsafe_allow_html=True)

    answers = [x[2] for x in st.session_state.answers]
    connections = habit_connections(answers)
    for left, relation, right in connections:
        st.markdown(
            f'<div class="card"><b>{left}</b> &nbsp; → &nbsp; <span class="pill">{relation}</span> &nbsp; → &nbsp; <b>{right}</b></div>',
            unsafe_allow_html=True
        )
    st.info("These are pattern explanations, not proof that one habit causes another.")

# -----------------------------
# AI Coach
# -----------------------------
elif st.session_state.page == "AI Coach":
    st.markdown('<div class="hero"><h1>🤖 AI Coach</h1><p>Ask about your digital habits and get practical, project-level guidance.</p></div>', unsafe_allow_html=True)

    history = get_chats(st.session_state.username)
    for role, msg in history[-12:]:
        with st.chat_message("user" if role == "user" else "assistant"):
            st.write(msg)

    prompt = st.chat_input("Ask: How can I reduce distractions?")
    if prompt:
        save_chat(st.session_state.username, "user", prompt)

        p = prompt.lower()
        if "screen" in p and ("reduce" in p or "less" in p):
            reply = "Try one planned screen-free block each day and review your progress after a few days."
        elif "notification" in p or "distraction" in p:
            reply = "Start with non-essential notifications. During focused work, keep only the alerts you actually need."
        elif "sleep" in p or "night" in p:
            reply = "Try a consistent screen-free wind-down before sleep and compare your next assessment with this one."
        elif "study" in p or "focus" in p:
            reply = "Use a defined study session, close entertainment apps, and take intentional breaks instead of reactive checks."
        elif "score" in p:
            reply = f"Your latest digital-balance indicator is {st.session_state.last_score:.0f}/100. Open Analysis to see the factors behind it." if st.session_state.last_score is not None else "Complete an assessment first."
        else:
            reply = "Based on the project model, focus on one small, measurable habit change and then reassess it."
        save_chat(st.session_state.username, "assistant", reply)
        st.rerun()

# -----------------------------
# Progress & Calendar
# -----------------------------
elif st.session_state.page == "Progress & Calendar":
    st.markdown('<div class="hero"><h1>📅 Progress & Calendar</h1><p>See how your self-reported digital-balance indicator changes over time.</p></div>', unsafe_allow_html=True)

    hist = get_history(st.session_state.username)
    if not hist:
        st.info("Complete an assessment to start your progress history.")
    else:
        dates = [datetime.fromisoformat(x["date"]) for x in hist]
        scores = [x["score"] for x in hist]
        plot_line(dates, scores, "Assessment history")

        df = pd.DataFrame({"Date": dates, "Indicator": scores})
        df["Change"] = df["Indicator"].diff().round(1)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### 🗓️ Recent assessment calendar")
        for d, s in reversed(list(zip(dates, scores))[-10:]):
            st.markdown(
                f'<div class="card"><b>{d.strftime("%d %b %Y")}</b> · Indicator {s:.0f}/100</div>',
                unsafe_allow_html=True
            )

# -----------------------------
# What-If Lab
# -----------------------------
elif st.session_state.page == "What-If Lab":
    st.markdown('<div class="hero"><h1>🧪 What-If Lab</h1><p>Explore an illustrative scenario before changing a habit.</p></div>', unsafe_allow_html=True)

    base = st.session_state.last_score if st.session_state.last_score is not None else 60.0
    change = st.slider("Illustrative improvement in one selected habit", 0, 50, 10, 5)
    projected = min(100, round(base + change * 0.45, 1))

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Current indicator", f"{base:.0f}")
    with c2:
        st.metric("Illustrative scenario", f"{projected:.0f}", f"+{projected-base:.0f}")

    st.progress(projected / 100)
    st.caption("This is a scenario model, not a prediction. Real outcomes depend on behaviour and context.")

# -----------------------------
# Milestones
# -----------------------------
elif st.session_state.page == "Milestones":
    st.markdown('<div class="hero"><h1>🏆 Milestones</h1><p>Progress markers based on meaningful project actions.</p></div>', unsafe_allow_html=True)

    hist = get_history(st.session_state.username)
    milestones = [
        ("🌱 First Reflection", len(hist) >= 1, "Complete your first assessment."),
        ("🧭 Goal Explorer", len(hist) >= 1 and len(hist[-1]["goals"]) >= 3, "Explore at least three goals."),
        ("🤖 AI Explorer", len(get_chats(st.session_state.username)) >= 2, "Have a conversation with AI Coach."),
        ("📈 Progress Tracker", len(hist) >= 2, "Complete two assessments."),
        ("🔍 Explainability", st.session_state.last_score is not None and bool(st.session_state.last_factors), "View the factors behind your indicator."),
        ("🎯 Action Planner", bool(st.session_state.last_actions), "Generate a personalised action plan."),
    ]

    for title, unlocked, desc in milestones:
        status = "Unlocked" if unlocked else "Locked"
        st.markdown(
            f'<div class="card"><h3>{title} &nbsp; <span class="pill">{status}</span></h3><div class="small">{desc}</div></div>',
            unsafe_allow_html=True
        )

# -----------------------------
# Wellness Report
# -----------------------------
elif st.session_state.page == "Wellness Report":
    st.markdown('<div class="hero"><h1>📄 Personal Digital Wellness Report</h1><p>A concise summary you can keep as a record of your reflection.</p></div>', unsafe_allow_html=True)

    if st.session_state.last_score is None:
        st.info("Complete an assessment first.")
    else:
        report = make_report(
            st.session_state.username,
            st.session_state.last_score,
            st.session_state.last_goal_scores,
            st.session_state.selected_goals,
            st.session_state.last_factors,
            st.session_state.last_actions
        )
        st.text_area("Report preview", report, height=480)
        st.download_button(
            "⬇️ Download report",
            report,
            file_name="DigitalBalance_AI_Wellness_Report.txt",
            mime="text/plain",
            use_container_width=True
        )

# -----------------------------
# Privacy & Ethics
# -----------------------------
elif st.session_state.page == "Privacy & AI Ethics":
    st.markdown('<div class="hero"><h1>🔐 Privacy & AI Ethics</h1><p>Responsible technology is part of the project, not an afterthought.</p></div>', unsafe_allow_html=True)

    items = [
        ("Privacy first", "The app is designed around user-provided information rather than secret device monitoring."),
        ("Transparency", "The score uses a simple heuristic model so the project can explain what influenced it."),
        ("Human control", "Users choose their goals, provide their answers, and decide what actions to take."),
        ("No diagnosis", "DigitalBalance AI is an educational digital-wellbeing project, not a medical tool."),
        ("Fairness", "The same scoring logic is applied consistently to the provided responses."),
        ("Data awareness", "The demo stores account and assessment information in its local SQLite database."),
        ("SDG 3", "The project connects digital well-being with Good Health and Well-being."),
        ("SDG 4", "It can also support awareness and responsible digital learning."),
    ]
    for title, body in items:
        st.markdown(f'<div class="card"><h3>{title}</h3><div class="small">{body}</div></div>', unsafe_allow_html=True)

    st.info("Competition note: explain that this is a self-reported educational indicator, not a medical diagnosis or hidden monitoring system.")

# Footer
st.markdown("---")
st.markdown(
    '<div class="small" style="text-align:center;">DigitalBalance AI · Understand your digital life. Balance it better. · SDG 3 + Responsible AI</div>',
    unsafe_allow_html=True
)
