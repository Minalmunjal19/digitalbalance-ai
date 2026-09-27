import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ---------------- PAGE SETUP ----------------
st.set_page_config(
    page_title="DigitalBalance AI",
    page_icon="📱",
    layout="wide"
)

# ---------------- CUSTOM STYLE ----------------
st.markdown("""
<style>
.main-title {
    font-size: 42px;
    font-weight: 800;
}
.subtitle {
    font-size: 18px;
    color: #666;
}
.card {
    padding: 22px;
    border-radius: 18px;
    background: #f5f7fb;
    margin-bottom: 15px;
}
.big-score {
    font-size: 55px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "goals" not in st.session_state:
    st.session_state.goals = []

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "history" not in st.session_state:
    st.session_state.history = []

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# ---------------- QUESTION BANK ----------------

question_bank = {

"📱 Screen Time": [
("What is your average daily screen time?",
 ["Less than 2 hours", "2–4 hours", "4–6 hours", "6–8 hours", "More than 8 hours"]),
("What do you mainly use your phone for?",
 ["Study", "Social media", "Entertainment", "Gaming", "Communication"]),
("How often do you check your phone unnecessarily?",
 ["Rarely", "Sometimes", "Often", "Very often"]),
("Is your screen time higher than you want?",
 ["No", "Slightly", "Moderately", "A lot"]),
("When do you use your phone the most?",
 ["Morning", "Afternoon", "Evening", "Night"]),
("How much time do you spend on social media?",
 ["Very little", "Less than 1 hour", "1–2 hours", "2–4 hours", "More than 4 hours"]),
("How much entertainment/video content do you watch daily?",
 ["Very little", "Less than 1 hour", "1–2 hours", "2–4 hours", "More than 4 hours"]),
("Do you use your phone during meals or other activities?",
 ["Never", "Sometimes", "Often", "Almost always"])
],

"⚖️ Digital Balance": [
("How satisfied are you with your current digital habits?",
 ["Very satisfied", "Satisfied", "Neutral", "Unsatisfied", "Very unsatisfied"]),
("Do you use your phone longer than planned?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("What usually triggers extra phone use?",
 ["Boredom", "Notifications", "Stress", "Habit", "Friends"]),
("How difficult is it to put your phone away?",
 ["Very easy", "Easy", "Moderate", "Difficult", "Very difficult"]),
("How well can you control planned screen time?",
 ["Very well", "Well", "Sometimes", "Poorly", "Very poorly"]),
("How balanced is your online and offline time?",
 ["Very balanced", "Balanced", "Neutral", "Unbalanced", "Very unbalanced"]),
("What is your biggest digital distraction?",
 ["Social media", "Videos", "Gaming", "Messages", "Notifications"]),
("Which digital habit would you like to improve?",
 ["Screen time", "Social media", "Night use", "Notifications", "Focus"])
],

"📚 Study & Screen": [
("How much screen time is used for studying?",
 ["Less than 1 hour", "1–2 hours", "2–4 hours", "4–6 hours", "More than 6 hours"]),
("How often does your phone interrupt your study?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("How often do you use your phone for non-study activities while studying?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("When do you study most effectively?",
 ["Morning", "Afternoon", "Evening", "Night"]),
("How often do notifications appear during study?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("How often do you check your phone during breaks?",
 ["Never", "Rarely", "Sometimes", "Often", "Every break"]),
("Does social media make it harder to return to study?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("Which digital tools do you use for studying?",
 ["Videos", "Notes", "Educational apps", "Search", "AI tools"])
],

"🌙 Night Usage": [
("Do you use your phone after your planned bedtime?",
 ["Never", "Rarely", "Sometimes", "Often", "Every night"]),
("What do you mainly do on your phone at night?",
 ["Study", "Social media", "Videos", "Chatting", "Gaming"]),
("How often do you check your phone after going to bed?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("Does night usage last longer than planned?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("How long do you usually use your phone after bedtime?",
 ["0–15 min", "15–30 min", "30–60 min", "1–2 hours", "More than 2 hours"]),
("What is the main reason for late-night phone use?",
 ["Study", "Entertainment", "Social media", "Messages", "Habit"]),
("Does phone use delay your intended bedtime?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("Do you keep your phone near you while sleeping?",
 ["No", "Sometimes", "Usually", "Always"])
],

"🔔 Distraction Analyzer": [
("How often do notifications interrupt your study?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("How often do you switch between apps while studying?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("How often do you unlock your phone just to check it?",
 ["Never", "Rarely", "Sometimes", "Often", "Very often"]),
("What is your biggest distraction?",
 ["Social media", "Messages", "Videos", "Games", "Notifications"]),
("Do you check notifications immediately?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("Do you lose focus after checking your phone?",
 ["Never", "Rarely", "Sometimes", "Often", "Always"]),
("Which app category distracts you most?",
 ["Social media", "Entertainment", "Gaming", "Messaging", "Other"]),
("Is it difficult to return to study after checking your phone?",
 ["Very easy", "Easy", "Moderate", "Difficult", "Very difficult"])
]
}

# ---------------- FUNCTIONS ----------------

def get_limit():
    n = len(st.session_state.goals)

    limits = {
        1: 8,
        2: 12,
        3: 15,
        4: 18,
        5: 20
    }

    return limits.get(n, 8)


def build_questions():

    selected = st.session_state.goals
    result = []

    positions = {goal: 0 for goal in selected}

    while len(result) < get_limit():

        added = False

        for goal in selected:

            if len(result) >= get_limit():
                break

            pos = positions[goal]

            if pos < len(question_bank[goal]):

                q = question_bank[goal][pos]

                result.append({
                    "goal": goal,
                    "question": q[0],
                    "options": q[1]
                })

                positions[goal] += 1
                added = True

        if not added:
            break

    return result


def calculate_score():

    if not st.session_state.answers:
        return 0

    values = {
        "Never": 5,
        "Rarely": 4,
        "Sometimes": 3,
        "Often": 2,
        "Very often": 1,
        "Always": 1,
        "Very satisfied": 5,
        "Satisfied": 4,
        "Neutral": 3,
        "Unsatisfied": 2,
        "Very unsatisfied": 1,
        "Very balanced": 5,
        "Balanced": 4,
        "Unbalanced": 2,
        "Very unbalanced": 1,
        "Very easy": 5,
        "Easy": 4,
        "Moderate": 3,
        "Difficult": 2,
        "Very difficult": 1,
        "No": 5,
        "Slightly": 4,
        "Moderately": 3,
        "A lot": 1,
        "Never": 5
    }

    scores = []

    for answer in st.session_state.answers.values():

        if answer in values:
            scores.append(values[answer])

        elif "Less than" in answer:
            scores.append(5)

        elif "2–4" in answer:
            scores.append(4)

        elif "4–6" in answer:
            scores.append(3)

        elif "6–8" in answer:
            scores.append(2)

        elif "More than" in answer:
            scores.append(1)

        elif "1–2" in answer:
            scores.append(4)

        elif "2–4" in answer:
            scores.append(3)

        else:
            scores.append(3)

    if not scores:
        return 0

    score = np.mean(scores) * 20

    return int(round(score))


def insight(score):

    if score >= 80:
        return "Your responses show relatively balanced digital habits. Keep monitoring patterns and maintain the habits that work for you."

    elif score >= 60:
        return "Your digital habits show some areas that could be improved. Small changes may help create more consistent balance."

    elif score >= 40:
        return "Your responses suggest several digital habits worth reviewing. Try identifying your biggest distractions and changing one habit at a time."

    else:
        return "Your responses show multiple areas for improvement. Focus on manageable changes such as reducing unnecessary checking and setting clear digital boundaries."

# ---------------- LOGIN ----------------

if not st.session_state.logged_in:

    st.markdown(
        '<div class="main-title">📱 DigitalBalance AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Understand your digital life. Balance it better.</div>',
        unsafe_allow_html=True
    )

    st.write("")

    st.info("AI-powered digital habit analysis for awareness and self-reflection.")

    name = st.text_input("Enter your name")

    if st.button("🚀 Start DigitalBalance AI", use_container_width=True):

        if name.strip():

            st.session_state.username = name.strip()
            st.session_state.logged_in = True
            st.rerun()

        else:

            st.warning("Please enter your name.")

    st.divider()

    st.caption("SDG 3 – Good Health and Well-being")
    st.caption("Privacy-first • Transparent • Responsible AI")

    st.stop()

# ---------------- SIDEBAR ----------------

st.sidebar.title("📱 DigitalBalance AI")

st.sidebar.write(f"Welcome, **{st.session_state.username}**")

page = st.sidebar.radio(
    "Navigate",
    [
        "Dashboard",
        "Smart Questions",
        "Analysis",
        "What-If Lab",
        "My Progress",
        "Privacy & AI Ethics"
    ]
)

if st.sidebar.button("Log out"):

    st.session_state.logged_in = False
    st.rerun()

# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("📊 DigitalBalance AI")

    st.write(
        "Understand your digital habits through personalised questions, "
        "data analysis and interactive insights."
    )

    st.markdown("---")

    cols = st.columns(5)

    cards = [
        ("📱", "Screen Time"),
        ("⚖️", "Digital Balance"),
        ("📚", "Study & Screen"),
        ("🌙", "Night Usage"),
        ("🔔", "Distractions")
    ]

    for col, (icon, name) in zip(cols, cards):

        with col:

            st.markdown(
                f"""
                <div class="card">
                <h2>{icon}</h2>
                <b>{name}</b>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.subheader("🎯 Select your goals")

    selected = st.multiselect(
        "What would you like DigitalBalance AI to analyse?",
        list(question_bank.keys()),
        default=st.session_state.goals
    )

    st.session_state.goals = selected

    if selected:

        st.success(
            f"{len(selected)} goal(s) selected → "
            f"{get_limit()} smart questions will be generated."
        )

        if st.button("📝 Start Smart Questions", use_container_width=True):

            st.session_state.answers = {}
            st.session_state.page = "Smart Questions"
            st.rerun()

    else:

        st.info("Select at least one goal to begin.")

    st.markdown("---")

    st.subheader("🌍 Sustainable Development Goals")

    st.write(
        "**SDG 3 – Good Health and Well-being**  \n"
        "DigitalBalance AI promotes awareness of digital habits and "
        "encourages healthier technology use."
    )

    st.write(
        "**SDG 4 – Quality Education**  \n"
        "The project also explores how digital distractions can affect study routines."
    )

# ---------------- QUESTIONS ----------------

elif page == "Smart Questions":

    st.title("🧠 Smart Digital Habit Questions")

    if not st.session_state.goals:

        st.warning("Please select at least one goal from Dashboard.")

    else:

        questions = build_questions()

        st.write(
            f"Answer {len(questions)} personalised questions based on your selected goals."
        )

        with st.form("questions_form"):

            for i, q in enumerate(questions):

                st.markdown(f"### Q{i+1}. {q['question']}")

                answer = st.radio(
                    "Select one:",
                    q["options"],
                    key=f"q_{i}"
                )

                st.session_state.answers[i] = answer

                st.divider()

            submitted = st.form_submit_button(
                "📊 Analyse My Digital Habits",
                use_container_width=True
            )

        if submitted:

            score = calculate_score()

            st.session_state.history.append({
                "Date": datetime.now().strftime("%d %b %Y"),
                "Score": score,
                "Goals": len(st.session_state.goals)
            })

            st.session_state.page = "Analysis"

            st.success("Analysis completed!")

            st.rerun()

# ---------------- ANALYSIS ----------------

elif page == "Analysis":

    st.title("📊 Your Digital Balance Analysis")

    if not st.session_state.answers:

        st.info("Complete the Smart Questions first.")

    else:

        score = calculate_score()

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                f"""
                <div class="card">
                <div class="big-score">{score}/100</div>
                <p>Digital Balance Indicator</p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.info(
                "This is a non-medical self-reflection indicator. "
                "It does not diagnose health conditions."
            )

        st.subheader("📈 Response Overview")

        answer_values = []

        for answer in st.session_state.answers.values():

            if answer in ["Never", "Rarely"]:
                answer_values.append(5)

            elif answer == "Sometimes":
                answer_values.append(3)

            elif answer in ["Often", "Very often", "Always"]:
                answer_values.append(2)

            else:
                answer_values.append(3)

        chart_data = pd.DataFrame({
            "Question": range(1, len(answer_values) + 1),
            "Response Score": answer_values
        })

        st.line_chart(
            chart_data.set_index("Question")
        )

        st.subheader("💡 Personalised Insight")

        st.success(insight(score))

        st.subheader("🎯 Suggested focus areas")

        suggestions = [
            "Set specific phone-free study periods.",
            "Review unnecessary notifications.",
            "Create a consistent night-time digital routine.",
            "Track which apps consume the most time.",
            "Make small changes instead of trying to change everything at once."
        ]

        for suggestion in suggestions:

            st.write("•", suggestion)

# ---------------- WHAT IF ----------------

elif page == "What-If Lab":

    st.title("🧪 What-If Lab")

    st.write(
        "Explore how changing a digital habit could change your estimated daily usage."
    )

    current_hours = st.slider(
        "Current daily screen time",
        1.0,
        12.0,
        6.0,
        0.5
    )

    reduction = st.slider(
        "Reduce screen time by",
        0.0,
        50.0,
        10.0,
        5.0
    )

    new_hours = current_hours * (1 - reduction / 100)
    saved = current_hours - new_hours

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Current",
        f"{current_hours:.1f} hrs"
    )

    col2.metric(
        "What-If",
        f"{new_hours:.1f} hrs"
    )

    col3.metric(
        "Potential time saved",
        f"{saved:.1f} hrs/day"
    )

    st.info(
        "This simulator is an estimate for exploration, not a prediction of behaviour."
    )

# ---------------- PROGRESS ----------------

elif page == "My Progress":

    st.title("📈 My Progress")

    if not st.session_state.history:

        st.info(
            "Complete an analysis to start building your history."
        )

    else:

        history_df = pd.DataFrame(
            st.session_state.history
        )

        st.dataframe(
            history_df,
            use_container_width=True
        )

        st.subheader("Score Trend")

        st.line_chart(
            history_df["Score"]
        )

# ---------------- PRIVACY ----------------

elif page == "Privacy & AI Ethics":

    st.title("🔐 Privacy & AI Ethics")

    st.write(
        "DigitalBalance AI is designed around responsible and transparent AI use."
    )

    principles = {
        "🔒 Privacy":
        "The project should only use information provided by the user.",

        "👁️ Transparency":
        "Users should understand what data is being analysed and why.",

        "⚖️ Fairness":
        "Insights should avoid unfair assumptions about different users.",

        "🧑‍💻 Human Control":
        "AI suggestions should support user decisions rather than replace them.",

        "🤖 Responsible AI":
        "The system should avoid presenting its score as a medical diagnosis."
    }

    for title, description in principles.items():

        st.markdown(
            f"""
            <div class="card">
            <h3>{title}</h3>
            <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.subheader("🌍 SDG Connection")

    st.write(
        "**SDG 3 – Good Health and Well-being:** "
        "Promotes awareness of digital habits."
    )

    st.write(
        "**SDG 4 – Quality Education:** "
        "Highlights the relationship between digital distractions and study routines."
    )

# ---------------- FOOTER ----------------

st.markdown("---")

st.caption(
    "DigitalBalance AI • Understand your digital life. Balance it better."
)
