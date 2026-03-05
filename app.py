import streamlit as st
import sqlite3
import matplotlib.pyplot as plt

st.set_page_config(page_title="HerHeart", layout="centered")

# ------------------- UI STYLE -------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>

html, body, [class*="css"]  {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background: linear-gradient(180deg,#ffe6f2,#ffcce6);
}

/* text */
html, body, p, div, span, label {
    color:#33001a !important;
}

/* headings */
h1,h2,h3 {
    color:#b30059 !important;
}

/* button style */
.stButton>button {
    border-radius:30px;
    height:3em;
    background:linear-gradient(45deg,#ff4da6,#ff1a75);
    color:white;
    font-weight:600;
    border:none;
    transition:0.3s;
}

.stButton>button:hover{
transform:scale(1.05);
}

/* animated heart */
@keyframes beat{
0%{transform:scale(1);}
50%{transform:scale(1.25);}
100%{transform:scale(1);}
}

.heart{
animation:beat 1s infinite;
display:inline-block;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("herheart.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
username TEXT PRIMARY KEY,
password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS health_history(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
score INTEGER,
risk_level TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS appointments(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
name TEXT,
urgency TEXT
)
""")

conn.commit()

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False

if "username" not in st.session_state:
    st.session_state.username=""

if "chat_history" not in st.session_state:
    st.session_state.chat_history=[]

# ---------------- AUTH ----------------
def auth():

    st.markdown("""
    <h1 style='text-align:center;'>
    <span class="heart">💗</span> HerHeart <span class="heart">💗</span>
    </h1>
    """,unsafe_allow_html=True)

    option=st.radio("Select Option",["Login","Sign Up"],horizontal=True)

    username=st.text_input("👤 Username")
    password=st.text_input("🔑 Password",type="password")

    if option=="Sign Up":
        if st.button("✨ Create Account"):
            try:
                cursor.execute("INSERT INTO users VALUES (?,?)",(username,password))
                conn.commit()
                st.success("Account created. Please login.")
            except:
                st.error("Username already exists")

    if option=="Login":
        if st.button("🚀 Login"):
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
            if cursor.fetchone():
                st.session_state.logged_in=True
                st.session_state.username=username
                st.rerun()
            else:
                st.error("Invalid login")

# ---------------- AI RESPONSE ----------------
def generate_ai_response(text):

    text=text.lower()

    if "chest" in text:
        return "Chest pain may be serious. Please seek emergency care."
    elif "fatigue" in text:
        return "Unusual fatigue can sometimes be heart-related."
    elif "breath" in text:
        return "Shortness of breath should be evaluated by a doctor."
    else:
        return "For accurate diagnosis, consult a medical professional."

# ---------------- MAIN APP ----------------
def main_app():

    st.markdown(f"## 💗 Welcome {st.session_state.username}")

    menu=st.radio(
        "Navigation",
        ["🏠 Home","🧬 Risk Factors","🩺 Symptoms","🤖 AI Chat","📊 Dashboard","👩‍⚕ Doctor"],
        horizontal=True
    )

# ---------------- HOME ----------------
    if menu=="🏠 Home":

        st.write("💗 Women-focused cardiovascular health system")
        st.write("This tool does not replace professional diagnosis")

# ---------------- RISK FACTORS ----------------
    elif menu=="🧬 Risk Factors":

        diabetes=st.checkbox("Type 2 Diabetes")
        bp=st.checkbox("High Blood Pressure")
        cholesterol=st.checkbox("High Cholesterol")
        smoking=st.checkbox("Smoking")
        weight=st.checkbox("Overweight")
        pregnancy=st.checkbox("Pregnancy Complications")
        pcos=st.checkbox("PCOS")

        if st.button("💾 Save Risk Factors"):

            score=0

            for f in [diabetes,bp,cholesterol,smoking,weight]:
                if f:
                    score+=2

            for f in [pregnancy,pcos]:
                if f:
                    score+=3

            st.session_state.base_risk=score
            st.success("Risk factors saved")

# ---------------- SYMPTOMS ----------------
    elif menu=="🩺 Symptoms":

        chest=st.checkbox("Chest Pain")
        breath=st.checkbox("Shortness of Breath")
        fatigue=st.checkbox("Unusual Fatigue")
        nausea=st.checkbox("Nausea")

        if st.button("📊 Calculate Risk"):

            symptom_score=sum([chest,breath,fatigue,nausea])*2
            base=st.session_state.get("base_risk",0)

            total=base+symptom_score

            # 💗 LIVE RISK METER
            st.subheader("💗 Heart Risk Meter")
            st.progress(min(total/20,1.0))
            st.write(f"Risk Score: {total}/20")

            if total>=15:
                level="High"
                st.error("High Risk – Seek medical attention immediately")
            elif total>=8:
                level="Moderate"
                st.warning("Moderate Risk – Schedule doctor visit")
            else:
                level="Low"
                st.success("Low Risk")

            cursor.execute(
            "INSERT INTO health_history (username,score,risk_level) VALUES (?,?,?)",
            (st.session_state.username,total,level)
            )

            conn.commit()

# ---------------- AI CHAT ----------------
    elif menu=="🤖 AI Chat":

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt=st.chat_input("💬 Ask about heart health")

        if prompt:

            st.session_state.chat_history.append({"role":"user","content":prompt})

            reply=generate_ai_response(prompt)

            st.session_state.chat_history.append({"role":"assistant","content":reply})

            st.rerun()

# ---------------- DASHBOARD ----------------
    elif menu=="📊 Dashboard":

        cursor.execute("SELECT risk_level FROM health_history WHERE username=?",(st.session_state.username,))
        records=cursor.fetchall()

        if records:

            levels=[r[0] for r in records]

            st.write("Latest Result:",levels[-1])

            # ❤️ HEART ANIMATION
            st.markdown("""
            <div style='text-align:center;font-size:60px;' class='heart'>❤️</div>
            """,unsafe_allow_html=True)

            fig,ax=plt.subplots()

            ax.pie(
            [levels.count("Low"),levels.count("Moderate"),levels.count("High")],
            labels=["Low","Moderate","High"],
            autopct="%1.1f%%"
            )

            ax.set_title("Risk Distribution")

            st.pyplot(fig)

        else:
            st.info("No data available")

# ---------------- DOCTOR ----------------
    elif menu=="👩‍⚕ Doctor":

        name=st.text_input("Full Name")

        urgency=st.selectbox(
        "Urgency Level",
        ["Routine","Soon","Emergency"]
        )

        if st.button("📅 Submit Appointment"):

            cursor.execute(
            "INSERT INTO appointments (username,name,urgency) VALUES (?,?,?)",
            (st.session_state.username,name,urgency)
            )

            conn.commit()

            if urgency=="Emergency":
                st.error("Emergency selected. Go to nearest hospital immediately.")
            else:
                st.success("Appointment request submitted")

# ---------------- LOGOUT ----------------
    if st.button("🚪 Logout"):

        st.session_state.logged_in=False
        st.session_state.chat_history=[]
        st.rerun()

# ---------------- FLOW ----------------
if not st.session_state.logged_in:
    auth()
else:
    main_app()