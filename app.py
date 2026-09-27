import streamlit as st
import sqlite3
import hashlib
import json
from datetime import datetime, timedelta
import pandas as pd

# ============================================================
# DigitalBalance AI — single-file Streamlit exhibition app
# ============================================================

st.set_page_config(
    page_title="DigitalBalance AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_FILE = "digitalbalance.db"

GOALS = {
    "📱 Screen Time": [
        ("Average daily screen time?", ["Under 2 hours","2–4 hours","4–6 hours","6–8 hours","More than 8 hours"]),
        ("Main screen activity?", ["Study","Social media","Entertainment/video","Gaming","Communication"]),
        ("How often do you check your phone unnecessarily?", ["Rarely","Sometimes","Often","Very often"]),
        ("Is your screen time higher than you want?", ["No","Slightly","Moderately","A lot"]),
        ("When do you use your phone most?", ["Morning","Afternoon","Evening","Late night"]),
        ("How much time goes to social media?", ["Almost none","Under 1 hour","1–2 hours","2–4 hours","More than 4 hours"]),
        ("How much entertainment/video do you watch?", ["Almost none","Under 1 hour","1–2 hours","2–4 hours","More than 4 hours"]),
        ("Do you use your phone during meals or other activities?", ["Never","Sometimes","Often","Very often"]),
    ],
    "⚖️ Digital Balance": [
        ("How satisfied are you with your digital habits?", ["Very satisfied","Satisfied","Neutral","Dissatisfied","Very dissatisfied"]),
        ("Do you use your phone longer than planned?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("What usually triggers extra phone use?", ["Boredom","Stress","Notifications","Habit","Social media"]),
        ("How difficult is it to put your phone away?", ["Very easy","Easy","Moderate","Difficult","Very difficult"]),
        ("How well can you control planned screen time?", ["Very well","Well","Sometimes","Poorly","Very poorly"]),
        ("How balanced is your online and offline time?", ["Very balanced","Balanced","Neutral","Unbalanced","Very unbalanced"]),
        ("What is your biggest digital distraction?", ["Social media","Videos","Games","Messages","Notifications"]),
        ("Which habit would you most like to improve?", ["Screen time","Social media","Night use","Notifications","Focus"]),
    ],
    "📚 Study & Screen": [
        ("How much screen time is used for study?", ["Under 1 hour","1–2 hours","2–4 hours","4–6 hours","More than 6 hours"]),
        ("How often does your phone interrupt study?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("How often do you use your phone for non-study activities while studying?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("When do you study most effectively?", ["Morning","Afternoon","Evening","Late night"]),
        ("How often do notifications appear during study?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("How often do you check your phone during study breaks?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("Does social media make it harder to return to study?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("Which digital tools do you use for study?", ["Videos","Search","Educational apps","Notes/PDFs","AI tools"]),
    ],
    "🌙 Night Usage": [
        ("Do you use your phone after your planned bedtime?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("What do you mainly do on your phone at night?", ["Study","Social media","Videos","Chat","Games"]),
        ("How often do you check your phone after getting into bed?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("Is night usage longer than you planned?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("How long do you usually use your phone after bedtime?", ["None","Under 30 min","30–60 min","1–2 hours","More than 2 hours"]),
        ("Why do you stay on your phone late?", ["Study","Entertainment","Social media","Chatting","Habit"]),
        ("Does phone use delay your intended bedtime?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("Do you keep your phone near you while sleeping?", ["Never","Sometimes","Usually","Always"]),
    ],
    "🔔 Distraction Analyzer": [
        ("How often do notifications interrupt your study?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("How often do you switch between apps while studying?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("How often do you unlock your phone just to check it?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("What is your biggest distraction?", ["Social media","Videos","Games","Messages","Notifications"]),
        ("Do you check notifications immediately?", ["Never","Rarely","Sometimes","Often","Always"]),
        ("Do you lose focus after checking your phone?", ["Never","Rarely","Sometimes","Often","Very often"]),
        ("Which app category distracts you most?", ["Social media","Video","Games","Messaging","Other"]),
        ("How difficult is it to return to study after checking?", ["Very easy","Easy","Moderate","Difficult","Very difficult"]),
    ],
}

# ---------- Database ----------
def db():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS assessments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        created_at TEXT NOT NULL,
        goals TEXT NOT NULL,
        answers TEXT NOT NULL,
        score REAL NOT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        created_at TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL
    )""")
    con.commit()
    con.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def create_user(username, password):
    con = db()
    try:
        con.execute(
            "INSERT INTO users VALUES(?,?,?)",
            (username.strip().lower(), hash_password(password), datetime.now().isoformat())
        )
        con.commit()
        return True, "Account created."
    except sqlite3.IntegrityError:
        return False, "That username already exists."
    finally:
        con.close()

def check_login(username, password):
    con = db()
    row = con.execute(
        "SELECT password_hash FROM users WHERE username=?",
        (username.strip().lower(),)
    ).fetchone()
    con.close()
    return row is not None and row[0] == hash_password(password)

def save_assessment(username, goals, answers, score):
    con = db()
    con.execute(
        "INSERT INTO assessments(username,created_at,goals,answers,score) VALUES(?,?,?,?,?)",
        (username, datetime.now().isoformat(), json.dumps(goals), json.dumps(answers), score)
    )
    con.commit()
    con.close()

def get_history(username):
    con = db()
    rows = con.execute(
        "SELECT id,created_at,goals,answers,score FROM assessments WHERE username=? ORDER BY created_at",
        (username,)
    ).fetchall()
    con.close()
    return rows

def save_chat(username, question, answer):
    con = db()
    con.execute(
        "INSERT INTO chats(username,created_at,question,answer) VALUES(?,?,?,?)",
        (username, datetime.now().isoformat(), question, answer)
    )
    con.commit()
    con.close()

def get_chats(username):
    con = db()
    rows = con.execute(
        "SELECT created_at,question,answer FROM chats WHERE username=? ORDER BY created_at DESC",
        (username,)
    ).fetchall()
    con.close()
    return rows

# ---------- Theme ----------
if "theme" not in st.session_state:
    st.session_state.theme = "Light"

if st.session_state.theme == "Dark":
    bg = "#0b1220"; card = "#111c2e"; text = "#f8fafc"; muted = "#b7c2d4"
    border = "#2a3a52"; input_bg = "#17243a"
else:
    bg = "#f5f7fb"; card = "#ffffff"; text = "#172033"; muted = "#64748b"
    border = "#dbe2ea"; input_bg = "#ffffff"

st.markdown(f"""
<style>
.stApp {{ background:{bg}; }}
.block-container {{max-width:1150px; padding-top:1.5rem; padding-bottom:3rem;}}
h1,h2,h3,h4,p,span,label {{color:{text} !important;}}
.db-card {{background:{card}; border:1px solid {border}; border-radius:20px; padding:22px; margin-bottom:18px;}}
.small {{color:{muted} !important;}}
.stTextInput input, .stNumberInput input {{background:{input_bg} !important; color:{text} !important;}}
div[data-testid="stMetric"] {{background:{card}; border:1px solid {border}; border-radius:16px; padding:14px;}}
div[data-baseweb="select"] > div {{background:{input_bg} !important;}}
button[kind="primary"] {{border-radius:12px;}}
</style>
""", unsafe_allow_html=True)

# ---------- Session ----------
for k, v in {
    "logged_in": False,
    "username": "",
    "page": "Dashboard",
    "selected_goals": [],
    "answers": {},
    "last_result": None,
    "profile_name": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- Question selection ----------
def build_questions(goals):
    # Balanced round-robin selection, capped for usability.
    limits = {1: 8, 2: 12, 3: 15, 4: 18, 5: 20}
    target = limits.get(len(goals), 20)
    pointers = {g: 0 for g in goals}
    result = []
    seen = set()
    while len(result) < target:
        added = False
        for g in goals:
            if pointers[g] >= len(GOALS[g]):
                continue
            q, options = GOALS[g][pointers[g]]
            pointers[g] += 1
            key = q.lower().strip()
            if key not in seen:
                result.append((g, q, options))
                seen.add(key)
                added = True
            if len(result) >= target:
                break
        if not added:
            break
    return result

def risk_value(answer):
    a = answer.lower()
    if any(x in a for x in ["never","rarely","under 2","under 1 hour","almost none","very satisfied","very well","very easy","very balanced","no"]):
        return 0
    if any(x in a for x in ["sometimes","2–4 hours","1–2 hours","satisfied","well","easy","balanced","slightly"]):
        return 1
    if any(x in a for x in ["often","4–6 hours","30–60","moderate","neutral","moderately","afternoon","evening"]):
        return 2
    if any(x in a for x in ["very often","6–8 hours","2–4 hours","difficult","dissatisfied","poorly","unbalanced","a lot"]):
        return 3
    if any(x in a for x in ["more than 8","more than 4","more than 6","very difficult","very dissatisfied","very poorly","very unbalanced","always"]):
        return 4
    return 1

def calculate_score(answers):
    if not answers:
        return 0
    vals = [risk_value(v) for v in answers.values()]
    return round(100 - (sum(vals) / (len(vals) * 4) * 100), 1)

def goal_score(goal, answers):
    vals = [risk_value(v) for q, v in answers.items() if q in [x[0] for x in GOALS[goal]]]
    if not vals:
        return 0
    return round(100 - (sum(vals)/(len(vals)*4)*100), 1)

def score_message(score):
    if score >= 80:
        return "Your current digital habits look relatively balanced. Keep monitoring the patterns."
    if score >= 60:
        return "Your habits show some areas that may benefit from small, consistent changes."
    if score >= 40:
        return "Several digital habits are creating noticeable friction. Focus on one or two changes first."
    return "Your answers show several areas worth reviewing. Start with small, realistic changes."

def chatbot_answer(question, latest_answers):
    q = question.lower()
    if not question.strip():
        return "Ask me something about your digital habits, study focus, screen time, distractions or night usage."
    if any(x in q for x in ["screen time","phone","mobile"]):
        return "Try identifying one high-use period and setting a short phone-free block there. Review your next assessment to see whether the pattern changes."
    if any(x in q for x in ["study","focus","distraction","concentrate"]):
        return "For study sessions, reduce interruptions first: silence non-essential notifications, keep only study apps open, and use a defined break instead of checking randomly."
    if any(x in q for x in ["sleep","night","bedtime","late"]):
        return "A practical first step is to create a consistent phone-free period before your planned bedtime and keep the phone away from the immediate study/sleep area."
    if any(x in q for x in ["social","instagram","reels","youtube","video"]):
        return "Notice when entertainment becomes automatic rather than intentional. A time boundary plus a planned alternative activity can make the change easier."
    if any(x in q for x in ["notification","alert"]):
        return "Group non-urgent notifications and turn off alerts that repeatedly interrupt your study or focus periods."
    if latest_answers:
        return "Based on your recent assessment, choose one behaviour to change first, then compare your next weekly result with this one."
    return "I can help you think through screen time, study focus, notifications, night usage and digital balance."

# ---------- Login ----------
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align:center; padding:45px 10px 20px;">
      <h1>⚖️ DigitalBalance AI</h1>
      <p>Understand your digital life. Balance it better.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "✨ Create account"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True, type="primary")
        if submit:
            if check_login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username.strip().lower()
                st.session_state.page = "Dashboard"
                st.rerun()
            else:
                st.error("Incorrect username or password.")

    with tab2:
        with st.form("signup_form"):
            new_user = st.text_input("Choose a username")
            new_pass = st.text_input("Create a password", type="password")
            confirm = st.text_input("Confirm password", type="password")
            create = st.form_submit_button("Create account", use_container_width=True, type="primary")
        if create:
            if len(new_user.strip()) < 3:
                st.error("Username must be at least 3 characters.")
            elif len(new_pass) < 6:
                st.error("Password should be at least 6 characters.")
            elif new_pass != confirm:
                st.error("Passwords do not match.")
            else:
                ok, msg = create_user(new_user, new_pass)
                if ok:
                    st.success("Account created. Go to Login.")
                else:
                    st.error(msg)

    st.stop()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## ⚖️ DigitalBalance AI")
    st.caption(f"Signed in as **{st.session_state.username}**")
    st.divider()

    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
        st.rerun()
    if st.button("🧠 Smart Questions", use_container_width=True):
        st.session_state.page = "Questions"
        st.rerun()
    if st.button("📊 Analysis", use_container_width=True):
        st.session_state.page = "Analysis"
        st.rerun()
    if st.button("🤖 AI Chatbot", use_container_width=True):
        st.session_state.page = "Chatbot"
        st.rerun()
    if st.button("📅 Weekly History", use_container_width=True):
        st.session_state.page = "Weekly"
        st.rerun()
    if st.button("📆 Monthly History", use_container_width=True):
        st.session_state.page = "Monthly"
        st.rerun()
    if st.button("🧪 What-If Lab", use_container_width=True):
        st.session_state.page = "What-If"
        st.rerun()
    if st.button("🔐 Privacy & AI Ethics", use_container_width=True):
        st.session_state.page = "Privacy"
        st.rerun()

    st.divider()
    theme = st.radio("Appearance", ["Light","Dark"], index=0 if st.session_state.theme=="Light" else 1)
    if theme != st.session_state.theme:
        st.session_state.theme = theme
        st.rerun()

    if st.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ---------- Header ----------
st.title("⚖️ DigitalBalance AI")
st.caption("Understand your digital life. Balance it better.")

# ---------- Dashboard ----------
if st.session_state.page == "Dashboard":
    st.subheader("👤 Profile & Goals")
    name = st.text_input("Your display name", value=st.session_state.profile_name)
    st.session_state.profile_name = name

    st.markdown("### What would you like to analyse?")
    goals = st.multiselect(
        "Choose one or more areas",
        list(GOALS.keys()),
        default=st.session_state.selected_goals,
        help="Choose as many areas as you want."
    )
    st.session_state.selected_goals = goals

    if goals:
        st.success(f"{len(goals)} goal(s) selected. Your questions will be personalised.")
        if st.button("Continue to Smart Questions →", type="primary", use_container_width=True):
            st.session_state.page = "Questions"
            st.rerun()
    else:
        st.info("Select at least one goal to begin.")

    st.markdown("### Your toolkit")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Goals selected", len(goals))
    hist = get_history(st.session_state.username)
    c2.metric("Assessments", len(hist))
    c3.metric("Chat sessions", len(get_chats(st.session_state.username)))
    c4.metric("Latest score", f"{hist[-1][4]:.0f}" if hist else "—")

# ---------- Questions ----------
elif st.session_state.page == "Questions":
    st.subheader("🧠 Smart Questions")
    if not st.session_state.selected_goals:
        st.warning("Choose your goals from Dashboard first.")
        if st.button("Go to Dashboard"):
            st.session_state.page = "Dashboard"; st.rerun()
    else:
        questions = build_questions(st.session_state.selected_goals)
        st.write(f"Answer {len(questions)} questions based on your current digital habits.")
        with st.form("assessment_form"):
            new_answers = {}
            for i, (goal, q, options) in enumerate(questions, 1):
                st.markdown(f"**{i}. {q}**")
                new_answers[q] = st.radio(
                    f"Goal: {goal}",
                    options,
                    key=f"q_{i}",
                    horizontal=False
                )
            submitted = st.form_submit_button("Analyse my digital habits →", type="primary", use_container_width=True)

        if submitted:
            score = calculate_score(new_answers)
            save_assessment(
                st.session_state.username,
                st.session_state.selected_goals,
                new_answers,
                score
            )
            st.session_state.answers = new_answers
            st.session_state.last_result = {
                "score": score,
                "answers": new_answers,
                "goals": st.session_state.selected_goals,
                "time": datetime.now().strftime("%d %b %Y, %I:%M %p")
            }
            st.session_state.page = "Analysis"
            st.rerun()

# ---------- Analysis ----------
elif st.session_state.page == "Analysis":
    st.subheader("📊 Analysis & Insights")
    result = st.session_state.last_result
    hist = get_history(st.session_state.username)

    if not result and hist:
        row = hist[-1]
        result = {"score": row[4], "answers": json.loads(row[3]), "goals": json.loads(row[2])}

    if not result:
        st.info("Complete an assessment first.")
    else:
        score = result["score"]
        a,b,c = st.columns(3)
        a.metric("Digital Balance Score", f"{score:.0f}/100")
        b.metric("Goals analysed", len(result["goals"]))
        c.metric("Questions answered", len(result["answers"]))

        st.progress(score/100)
        st.markdown(f'<div class="db-card"><h3>💡 Insight</h3><p>{score_message(score)}</p></div>', unsafe_allow_html=True)

        st.markdown("### Goal-wise analysis")
        goal_rows = []
        for g in result["goals"]:
            goal_rows.append({"Goal": g, "Score": goal_score(g, result["answers"])})
        gdf = pd.DataFrame(goal_rows)
        if not gdf.empty:
            st.bar_chart(gdf.set_index("Goal")["Score"], height=320)

        st.markdown("### Your answers")
        adf = pd.DataFrame([{"Question": q, "Answer": a} for q,a in result["answers"].items()])
        st.dataframe(adf, use_container_width=True, hide_index=True)

        st.info("This score is a digital-habit indicator, not a medical diagnosis.")

# ---------- Chatbot ----------
elif st.session_state.page == "Chatbot":
    st.subheader("🤖 Ask DigitalBalance AI")
    st.write("Ask about screen time, study focus, distractions, notifications, night usage or digital balance.")

    hist = get_history(st.session_state.username)
    latest_answers = json.loads(hist[-1][3]) if hist else {}

    for created, q, ans in reversed(get_chats(st.session_state.username)[:8]):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**DigitalBalance AI:** {ans}")
        st.divider()

    with st.form("chat_form"):
        question = st.text_input("Your question")
        send = st.form_submit_button("Ask AI", type="primary", use_container_width=True)
    if send:
        answer = chatbot_answer(question, latest_answers)
        save_chat(st.session_state.username, question, answer)
        st.rerun()

# ---------- Weekly ----------
elif st.session_state.page == "Weekly":
    st.subheader("📅 Weekly History")
    rows = get_history(st.session_state.username)
    if not rows:
        st.info("No history yet. Complete your first assessment.")
    else:
        data = pd.DataFrame([{
            "Date": datetime.fromisoformat(r[1]).strftime("%d %b"),
            "Score": r[4]
        } for r in rows])
        st.line_chart(data.set_index("Date")["Score"], height=320)
        st.dataframe(data, use_container_width=True, hide_index=True)
        if len(rows) >= 2:
            change = rows[-1][4] - rows[-2][4]
            st.metric("Change from previous assessment", f"{change:+.0f} points")
            st.caption("The chart shows saved assessment results over time. More frequent assessments make weekly trends more meaningful.")

# ---------- Monthly ----------
elif st.session_state.page == "Monthly":
    st.subheader("📆 Monthly History & Analysis")
    rows = get_history(st.session_state.username)
    if not rows:
        st.info("No history yet. Complete your first assessment.")
    else:
        records = []
        for r in rows:
            dt = datetime.fromisoformat(r[1])
            records.append({"Month": dt.strftime("%b %Y"), "Score": r[4]})
        df = pd.DataFrame(records)
        monthly = df.groupby("Month", sort=False)["Score"].mean().reset_index()
        st.line_chart(monthly.set_index("Month")["Score"], height=320)

        if len(monthly) >= 2:
            first = monthly.iloc[0]["Score"]
            last = monthly.iloc[-1]["Score"]
            delta = last - first
            if delta > 0:
                st.success(f"Your average recorded score increased by {delta:.0f} points across the shown period.")
            elif delta < 0:
                st.info(f"Your average recorded score changed by {delta:.0f} points across the shown period. Review the goal-level results for context.")
            else:
                st.info("Your average recorded score is unchanged across the shown period.")
        st.dataframe(monthly, use_container_width=True, hide_index=True)

# ---------- What-If ----------
elif st.session_state.page == "What-If":
    st.subheader("🧪 What-If Lab")
    result = st.session_state.last_result
    if not result:
        st.info("Complete an assessment first.")
    else:
        current = result["score"]
        st.write(f"Current score: **{current:.0f}/100**")
        improvement = st.slider("What if you improved a few digital habits?", 0, 30, 10, 5)
        projected = min(100, current + improvement)
        st.metric("Illustrative projected score", f"{projected:.0f}/100", f"+{projected-current:.0f}")
        st.caption("This is an illustrative scenario, not a prediction. Actual results depend on future behaviour.")

# ---------- Privacy ----------
elif st.session_state.page == "Privacy":
    st.subheader("🔐 Privacy & AI Ethics")
    st.markdown("""
    <div class="db-card">
    <h3>Privacy-first design</h3>
    <ul>
      <li>Users choose what information to enter.</li>
      <li>The app does not secretly monitor device activity.</li>
      <li>Each account is separated by username.</li>
      <li>Passwords are stored as hashes rather than plain text.</li>
    </ul>
    </div>
    <div class="db-card">
    <h3>Responsible AI</h3>
    <ul>
      <li><b>Transparency:</b> users can see what is being analysed.</li>
      <li><b>Human control:</b> suggestions are not commands.</li>
      <li><b>Fairness:</b> the app avoids judging people by a single score.</li>
      <li><b>Safety:</b> the score is not a medical diagnosis.</li>
    </ul>
    </div>
    <div class="db-card">
    <h3>🌱 SDG connection</h3>
    <p><b>SDG 3 — Good Health and Well-being</b><br>
    The project encourages awareness of digital habits and wellbeing.</p>
    <p><b>SDG 4 — Quality Education</b><br>
    Study-focus and distraction analysis supports more intentional learning.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("DigitalBalance AI • Understand your digital life. Balance it better.")

