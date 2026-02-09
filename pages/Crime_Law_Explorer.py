import google.generativeai as genai # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import streamlit as st # type: ignore
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


st.set_page_config(page_title="Law Explorer", layout="wide")

# ---------- STYLING ----------
st.markdown("""
<style>
/* App background */
.stApp {
    background-color: #E1E1E1;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #90B488;
}

/* Main cards */
.law-card {
    background-color: white;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0px 6px 15px rgba(0,0,0,0.12);
    margin-top: 20px;
}

/* Titles */
.law-title {
    color: #817D7E;
    font-weight: 700;
}

/* Buttons */
.stButton > button {
    background-color: #90B488;
    color: black;
    border-radius: 10px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #7AA76F;
}
</style>
""", unsafe_allow_html=True)


st.title("⚖️ Law Explorer")
def explain_law_ai(category, issue, data):
    prompt = f"""
    Explain the following Indian law in very simple words.

    Law category: {category}
    Issue: {issue}
    Section: {data['Section']}
    Punishment: {data['Punishment']}

    Explain:
    - What this law means
    - When it applies
    - Punishment in simple words
    """

    model =genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(prompt)
    return response.text

st.write("Understand Indian laws, sections and punishments")

# ---------- LAW DATA ----------
laws = {
    "Criminal Law": {
        "Rape": {
            "Section": "IPC 376 / BNS 63",
            "Punishment": "10 years to life imprisonment",
            "Jail": "10 years – Life",
            "Notes": "Stricter punishment if victim is minor"
        },
        "Murder": {
            "Section": "IPC 302",
            "Punishment": "Life imprisonment or death penalty",
            "Jail": "Life / Death",
            "Notes": "Depends on brutality & intent"
        }
    },

    "Civil Law": {
        "Recovery of Money": {
            "Section": "CPC 1908",
            "Punishment": "No jail (civil remedy)",
            "Jail": "None",
            "Notes": "Court orders payment"
        }
    },

    "Family Law": {
        "Divorce": {
            "Section": "Hindu Marriage Act",
            "Punishment": "No punishment",
            "Jail": "None",
            "Notes": "Mutual or contested"
        }
    },

    "Constitutional Law": {
        "Fundamental Rights": {
            "Section": "Articles 12–35",
            "Punishment": "Writ petition",
            "Jail": "None",
            "Notes": "Filed in High Court / Supreme Court"
        }
    },

    "Environmental Law": {
        "Pollution": {
            "Section": "Environment Protection Act",
            "Punishment": "Fine + imprisonment",
            "Jail": "Up to 5 years",
            "Notes": "Company directors also liable"
        }
    }
}

# ---------- CATEGORY SELECTION ----------
st.subheader("Select Law Category")

cols = st.columns(3)
selected_category = None

categories = list(laws.keys())

for i, cat in enumerate(categories):
    with cols[i % 3]:
       if st.button(cat):
         st.session_state.selected_category = cat
 

# ---------- ISSUE SELECTION ----------
if "selected_category" in st.session_state:
    selected_category = st.session_state.selected_category

    st.subheader(f"Issues under {selected_category}")

    issue = st.selectbox(
        "Select Issue",
        list(laws[selected_category].keys())
    )
    st.session_state.issue = issue


    if issue:
        data = laws[selected_category][issue]

        st.markdown(f"""
        <div class="law-card">
            <h3 class="law-title">{issue}</h3>
            <b>Section:</b> {data['Section']}<br><br>
            <b>Punishment:</b> {data['Punishment']}<br><br>
            <b>Jail Term:</b> {data['Jail']}<br><br>
            <b>Notes:</b> {data['Notes']}
        </div>
        """, unsafe_allow_html=True)

        # ---------- AI BUTTON ----------
        # ---------- AI BUTTON ----------
if st.button("🤖 Explain in simple words"):
    with st.spinner("AI is explaining the law..."):
       explanation = explain_law_ai(
    st.session_state.selected_category,
    st.session_state.issue,
    data
)
       st.success(explanation)
