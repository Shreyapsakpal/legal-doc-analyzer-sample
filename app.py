import streamlit as st # type: ignore
import google.generativeai as genai # type: ignore
from dotenv import load_dotenv # type: ignore
import os
from PyPDF2 import PdfReader # type: ignore
import docx # type: ignore
import sqlite3
import hashlib
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.pdfgen import canvas # pyright: ignore[reportMissingModuleSource]
import io

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


# ---------- SESSION STATE INIT ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "current_view" not in st.session_state:
    st.session_state.current_view = "App"

# ---------- AUTH SETUP ----------
def get_db():
    conn = sqlite3.connect("users.db", check_same_thread=False)
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()

    user_id = str(uuid.uuid4())
    try:
        c.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (user_id, username, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

def authenticate_user(username, password):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_password(password))
    )
    return c.fetchone()




# ---------- CONFIG ----------
load_dotenv()
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

st.set_page_config(page_title="AI Legal Analyzer", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    

    # ---------- SESSION STATE INIT ----------
if "sections" not in st.session_state:
    st.session_state.sections = {
        "entities": "",
        "parties": "",
        "dates": "",
        "clauses": "",
        "risks": "",
        "summary": ""
    }



# ---------- STYLING ----------
st.markdown("""
<style>
            <style>
            
/* Center main block and reduce width */
.block-container {
    max-width: 850px;
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
    margin: auto;
}

/* Fix text visibility */
h1, h2, h3, h4, h5, h6, p, label {
    color: #0A1931 !important;
}

/* Reduce card/container width feeling */
div[data-testid="stForm"] {
    padding: 1.5rem 1.5rem 1rem 1.5rem;
}

</style>


            
            

/* Sidebar background */
section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        rgba(220, 235, 255, 0.95),
        rgba(200, 225, 255, 0.95)
    );
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: #0A1931 !important;
}

/* Sidebar buttons */
section[data-testid="stSidebar"] .stButton > button {
    background-color: #8FB6FF;
    color: #0A1931;
    border-radius: 10px;
    font-weight: 600;
}

/* Sidebar expanders */
section[data-testid="stSidebar"] .streamlit-expanderHeader {
    background-color: rgba(255, 255, 255, 0.85);
    border-radius: 10px;
}

/* Sidebar divider lines */
section[data-testid="stSidebar"] hr {
    border-color: rgba(10, 25, 49, 0.1);
}

</style>
""", unsafe_allow_html=True)





# ---------- LOGIN / REGISTER ----------
if not st.session_state.logged_in:
    st.title("🔐 Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
     username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        user = authenticate_user(username, password)

        if user:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")




    with tab2:
        new_user = st.text_input("New Username")
        new_pass = st.text_input("New Password", type="password")

        if st.button("Register"):
            if create_user(new_user, new_pass):
                st.success("Account created! Please login.")
            else:
                st.error("Username already exists")
    st.stop() # ⛔ VERY IMPORTANT (stops analyzer from loading)

   # ---------- SIDEBAR : ACCOUNT DETAILS ----------
if st.session_state.logged_in:
    with st.sidebar:
        st.markdown("---")
        st.subheader("👤 Account Details")

        # 🔹 Account Info
        with st.expander("View Account Info", expanded=False):
            st.markdown(f"**Username:** {st.session_state.username}")
            st.markdown("**Password:** ********")

            st.markdown("---")

            if st.button("🚪 Logout"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()


    
# ---------- FILE TEXT EXTRACTION ----------
def extract_text(file):
    if file.type == "application/pdf":
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])

    elif file.type == "text/plain":
        return file.read().decode("utf-8")

    return ""


# ---------- AI FUNCTION ----------
def analyze_legal_text(text):
   
   prompt = f"""
You are a legal assistant.

Read the legal document below and explain it in VERY SIMPLE words.

FORMAT THE RESPONSE STRICTLY LIKE THIS (DO NOT CHANGE ORDER):


ENTITIES:
- Company names
- Client names
- Person names

KEY PARTIES:
- Service Provider
- Client

IMPORTANT DATES:
- Start date
- End date
- Any deadlines

CLAUSES:
- Important clauses explained simply

RISKS:
- Possible risks or penalties

SUMMARY:
- First, write a short paragraph (15–16 lines) explaining the document in simple language.
- Then give 10–12 bullet points highlighting key points.
- Do NOT make everything bullet points.


RULES:
- Simple English only
- Do NOT mix sections
- Do NOT repeat data
- Do NOT add extra headings

DOCUMENT:
{text}
"""


   model = genai.GenerativeModel("gemini-2.5-flash")
   response = model.generate_content(prompt)
   return response.text

def translate_summary(text, target_language):
    if target_language == "English":
        return text

    prompt = f"""
Translate the following legal summary into {target_language}.
Use very simple and clear language.
Do NOT add explanations.
Do NOT change meaning.

TEXT:
{text}
"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text



def split_sections(ai_text):

    # RESET sections before filling
    st.session_state.sections = {
        "entities": "",
        "parties": "",
        "dates": "",
        "clauses": "",
        "risks": "",
        "summary": ""
    }

    current = None
    for line in ai_text.splitlines():
        line_upper = line.upper()

        if "ENTITIES" in line_upper:
            current = "entities"
            continue
        elif "KEY PARTIES" in line_upper:
            current = "parties"
            continue
        elif "IMPORTANT DATES" in line_upper:
            current = "dates"
            continue
        elif "CLAUSES" in line_upper:
            current = "clauses"
            continue
        elif "RISKS" in line_upper:
            current = "risks"
            continue
        elif "SUMMARY" in line_upper:
            current = "summary"
            continue

        if current:
            st.session_state.sections[current] += line + "\n"

    return st.session_state.sections

    model = genai.GenerativeModel("gemini-2.5-flash")

    response = model.generate_content(prompt)
    return response.text

# ---------- INPUT ----------
st.subheader("Upload Document or Enter Text")

uploaded_file = st.file_uploader(
    "Upload PDF / DOCX / TXT",
    type=["pdf", "docx", "txt"]
)

manual_text = st.text_area(
    "OR paste legal text here",
    height=200
)

# ---------- ANALYZE BUTTON ----------
if st.button("🤖 Analyze Document"):
    with st.spinner("Analyzing legal content..."):
    

        if uploaded_file:
            text = extract_text(uploaded_file)
        else:
            text = manual_text

        if text.strip() == "":
            st.error("Please upload a file or enter text")
        else:
             # 2️⃣ Call Gemini
            with st.spinner("Analyzing legal document..."):
               with st.spinner("Analyzing legal document..."):
                 analysis_text = analyze_legal_text(text)

  

            # 3️⃣ STEP 3 STARTS HERE
            st.session_state.sections = split_sections(analysis_text)
            # ---------- PDF GENERATION ----------
def generate_full_analysis_pdf(sections):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    x = 40
    y = height - 40

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(x, y, "AI Legal Document Analysis")
    y -= 30

    def draw_section(title, content):
        nonlocal y
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(x, y, title)
        y -= 18

        pdf.setFont("Helvetica", 10)
        for line in content.split("\n"):
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 40
            pdf.drawString(x, y, line)
            y -= 14
        y -= 10

    draw_section("ENTITIES", sections["entities"])
    draw_section("KEY PARTIES", sections["parties"])
    draw_section("IMPORTANT DATES", sections["dates"])
    draw_section("CLAUSES", sections["clauses"])
    draw_section("RISKS", sections["risks"])
    draw_section("SUMMARY", sections["summary"])

    pdf.save()
    buffer.seek(0)
    return buffer


def render_highlighted_inline(section_text):
    lines = section_text.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if ":" in line:
            label, value = line.split(":", 1)
            label = label.replace("*", "").replace("-", "").strip()


            st.markdown(
                f"""
                <div style="margin-bottom:8px;">
                    <span style="
                        background-color:#F6E27F;
                        padding:2px 6px;
                        border-radius:4px;
                        font-weight:600;
                    ">
                        {label}:
                    </span>
                    <span style="margin-left:6px;">
                        {value.strip()}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"<div>{line}</div>", unsafe_allow_html=True)

        
           

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📌 Entities",
    "🏛️ Key Parties",
    "📅 Important Dates",
    "📜 Clauses",
    "⚠️ Risks",
    "📝 Summary"
])

with tab1:
    render_highlighted_inline(st.session_state.sections["entities"])


with tab2:
    render_highlighted_inline(st.session_state.sections["parties"])

with tab3:
    render_highlighted_inline(st.session_state.sections["dates"])

with tab4:
    render_highlighted_inline(st.session_state.sections["clauses"])

with tab5:
    render_highlighted_inline(st.session_state.sections["risks"])

with tab6:
    language = st.selectbox(
        "Select Summary Language",
        ["English", "Hindi", "Marathi", "German", "Japanese"]
    )
    summary_text = st.session_state.sections["summary"]

    if summary_text.strip():
        translated_summary = translate_summary(summary_text, language)
        render_highlighted_inline(translated_summary)


    if st.session_state.sections["summary"].strip():
        pdf_file = generate_full_analysis_pdf(st.session_state.sections)

        st.download_button(
            label="⬇️ Download Full Legal Analysis (PDF)",
            data=pdf_file,
            file_name="Legal_Document_Analysis.pdf",
            mime="application/pdf"
        )

   


