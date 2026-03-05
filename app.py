import streamlit as st
import sqlite3
import matplotlib.pyplot as plt

st.set_page_config(page_title="HerHeart", layout="centered")

# ------------------- DARK FONT PINK THEME -------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(180deg, #ffe6f2, #ffcce6);
}

/* FORCE DARK TEXT EVERYWHERE */
html, body, [class*="css"], p, div, span, label {
    color: #1a0010 !important;
    font-family: 'Segoe UI', sans-serif;
    font-weight: 500;
}

/* Headings */
h1, h2, h3 {
    color: #33001a !important;
    font-weight: 800;
}

/* Card Style */
.card {
    background-color: #fff0f7;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}

/* Buttons */
.stButton>button {
    width: 100%;
    border-radius: 30px;
    height: 3em;
    background-color: #b30059;
    color: white;
    font-weight: bold;
    border: none;
}

/* Input text */
input, textarea {
    color: #1a0010 !important;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("herheart.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS health_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    score INTEGER,
    risk_level TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    name TEXT,
    urgency TEXT
)
""")

conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------- AUTH ----------------
def auth():
    st.title("HerHeart")

    option = st.radio("Select Option", ["Login", "Sign Up"], horizontal=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if option == "Sign Up":
        if st.button("Create Account"):
            try:
                cursor.execute("INSERT INTO users VALUES (?, ?)", (username, password))
                conn.commit()
                st.success("Account created. Please login.")
            except:
                st.error("Username already exists.")

    if option == "Login":
        if st.button("Login"):
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            if cursor.fetchone():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid login.")

# ---------------- SIMPLE AI RESPONSE ----------------
def generate_ai_response(text):
    text = text.lower()

    if "chest" in text:
        return "Chest pain may be serious. Please seek emergency care if severe."
    elif "fatigue" in text:
        return "Unusual fatigue can sometimes be heart-related."
    elif "breath" in text:
        return "Shortness of breath should be evaluated by a doctor."
    else:
        return "For accurate diagnosis, consult a licensed medical professional."

# ---------------- MAIN APP ----------------
def main_app():
    st.title(f"Welcome {st.session_state.username}")

    menu = st.radio(
        "Navigation",
        ["Home", "Risk Factors", "Symptoms", "AI Chat", "Dashboard", "Doctor"],
        horizontal=True
    )

    if menu == "Home":
        st.write("Women-focused cardiovascular health system.")
        st.write("This tool does not replace professional diagnosis.")

    elif menu == "Risk Factors":
        diabetes = st.checkbox("Type 2 Diabetes")
        bp = st.checkbox("High Blood Pressure")
        cholesterol = st.checkbox("High Cholesterol")
        smoking = st.checkbox("Smoking")
        weight = st.checkbox("Overweight")
        pregnancy = st.checkbox("Pregnancy Complications")
        pcos = st.checkbox("PCOS")

        if st.button("Save Risk Factors"):
            score = 0
            for f in [diabetes, bp, cholesterol, smoking, weight]:
                if f:
                    score += 2
            for f in [pregnancy, pcos]:
                if f:
                    score += 3

            st.session_state.base_risk = score
            st.success("Risk factors saved.")

    elif menu == "Symptoms":
        chest = st.checkbox("Chest Pain")
        breath = st.checkbox("Shortness of Breath")
        fatigue = st.checkbox("Unusual Fatigue")
        nausea = st.checkbox("Nausea")

        if st.button("Calculate Risk"):
            symptom_score = sum([chest, breath, fatigue, nausea]) * 2
            base = st.session_state.get("base_risk", 0)
            total = base + symptom_score

            if total >= 15:
                level = "High"
                st.error("High Risk – Seek immediate medical attention.")
            elif total >= 8:
                level = "Moderate"
                st.warning("Moderate Risk – Schedule a doctor visit.")
            else:
                level = "Low"
                st.success("Low Risk")

            cursor.execute(
                "INSERT INTO health_history (username, score, risk_level) VALUES (?, ?, ?)",
                (st.session_state.username, total, level)
            )
            conn.commit()

    elif menu == "AI Chat":
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Ask about heart health")

        if prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            reply = generate_ai_response(prompt)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            st.rerun()

    elif menu == "Dashboard":
        cursor.execute("SELECT risk_level FROM health_history WHERE username=?", (st.session_state.username,))
        records = cursor.fetchall()

        if records:
            levels = [r[0] for r in records]
            st.write("Latest Result:", levels[-1])

            fig, ax = plt.subplots()
            ax.pie(
                [levels.count("Low"), levels.count("Moderate"), levels.count("High")],
                labels=["Low", "Moderate", "High"],
                autopct="%1.1f%%"
            )
            ax.set_title("Risk Distribution")
            st.pyplot(fig)
        else:
            st.info("No data available.")

    elif menu == "Doctor":
        name = st.text_input("Full Name")
        urgency = st.selectbox("Urgency Level", ["Routine", "Soon", "Emergency"])

        if st.button("Submit Appointment"):
            cursor.execute(
                "INSERT INTO appointments (username, name, urgency) VALUES (?, ?, ?)",
                (st.session_state.username, name, urgency)
            )
            conn.commit()

            if urgency == "Emergency":
                st.error("Emergency selected. Go to nearest hospital immediately.")
            else:
                st.success("Appointment request submitted.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.chat_history = []
        st.rerun()

# ---------------- APP FLOW ----------------
if not st.session_state.logged_in:
    auth()
else:
    main_app()