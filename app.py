import streamlit as st
import PyPDF2
import google.generativeai as genai
import re
from fpdf import FPDF

# ====== CUSTOM STYLE AND BACKGROUND ======
def set_bg_image():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgYCf7zQFjCI8WO8Y5XFuGpes5GuCXbyIQEA&s");
            background-size: cover;
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-position: center;
        }

        .block-container {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }

        h1, h2, h3, h4, h5, h6, p, div, span, label, textarea {
            color: black !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #001f3f !important;
        }
        section[data-testid="stSidebar"] * {
            color: white !important;
        }

        /* Outer wrapper of the Gemini API Key input */
        section[data-testid="stSidebar"] .stTextInput {
            border: 2px solid red !important;
            border-radius: 6px;
            padding: 4px;
            margin-bottom: 10px;
            
        }
        /* Inner input: transparent background, no border */
        section[data-testid="stSidebar"] .stTextInput input {
            color: blue !important;
            border: none !important;
            padding: 4px 8px;
        }
        section[data-testid="stSidebar"] .stTextInput svg {
            color: white !important;
            stroke: black !important;
        }

        /* Outer wrapper of the PDF uploader */
        section[data-testid="stSidebar"] .stFileUploader {
            border: 2px solid red!important;
            border-radius: 6px;
            padding: 4px;
            margin-bottom: 10px;
        }
        /* Inner uploader: transparent background, no border */
        section[data-testid="stSidebar"] .stFileUploader > div,
        section[data-testid="stSidebar"] .stFileUploader * {
            color: blue !important;
            border: none !important;
        }
        section[data-testid="stSidebar"] .stFileUploader button {
            background-color: #1a3c66 !important;
            color: blue !important;
            border: none !important;
            border-radius: 4px;
        }

        section[data-testid="stSidebar"] .stSelectbox div,
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stCheckbox,
        section[data-testid="stSidebar"] .stCheckbox label {
            color: white !important;
        }

        .stDownloadButton button {
            background-color: #1a3c66 !important;
            color: white !important;
            font-weight: bold;
        }

        .chat-bubble-user {
            background-color: #1877f2;
            color: white;
            padding: 10px 15px;
            border-radius: 15px;
            max-width: 70%;
            margin: 10px auto 10px 0;
            text-align: left;
            white-space: pre-wrap;
        }

        .chat-bubble-ai {
            background-color: #f1f0f0;
            color: black;
            padding: 10px 15px;
            border-radius: 15px;
            width: 100%;
            margin: 10px 0 10px 0;
            text-align: left;
            white-space: pre-wrap;
        }

        @media (prefers-color-scheme: light) {
            section[data-testid="stSidebar"] {
                background-color: #001f3f !important;
            }
            section[data-testid="stSidebar"] * {
                color: white !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_bg_image()

# ====== TEXT EXTRACTION FUNCTION ======
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text.strip()

# ====== CLEANUP FUNCTION ======
def clean_response(text):
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()

# ====== GEMINI HANDLERS ======
def generate_quiz(text, model):
    prompt = f"""
    From the following outline, generate 5 multiple-choice questions.
    Provide options (A to D) and mark the correct answer at the end of each question.

    Outline:
    {text}
    """
    response = model.generate_content(prompt)
    return clean_response(response.text)

def generate_assignment(text, model):
    prompt = f"""
    Based on the following semester outline, generate a detailed assignment prompt with title, objectives, and tasks.

    Outline:
    {text}
    """
    response = model.generate_content(prompt)
    return clean_response(response.text)

def ask_question(outline_text, user_query, model):
    prompt = f"Here is the semester outline:\n\n{outline_text}\n\nNow answer this user query: {user_query}"
    response = model.generate_content(prompt)
    return clean_response(response.text)

# ====== UTILITY TO CREATE PDF ======
def text_to_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest='S').encode('latin1')

# ====== SIDEBAR UI ======
st.sidebar.title("🧭 Semester Controls")
api_key = st.sidebar.text_input("🔑 Enter your Gemini API Key", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Upload Semester Outline (PDF only)", type=["pdf"])

st.sidebar.markdown("🚀 **Select Action(s)**")
ask_question_checked = st.sidebar.checkbox("Ask a Question")
generate_assignment_checked = st.sidebar.checkbox("Generate Assignment")
generate_quiz_checked = st.sidebar.checkbox("Generate Quiz")

# ====== MAIN DISPLAY ======
st.title("📘 Semester Assistant (Gemini AI)")
st.write("Interact with your uploaded semester outline using AI-powered Q&A, assignments, and quiz generation.")

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    with st.spinner("🔍 Extracting text from uploaded file..."):
        extracted_text = extract_text_from_pdf(uploaded_file)

    st.success("✅ Outline processed!")

    query = st.text_input("✏️ Enter your input:")

    if query:
        with st.spinner("💬 Getting response from Gemini..."):
            if ask_question_checked:
                resp = ask_question(extracted_text, query, model)
                st.session_state.conversation_history.insert(0, (f"[Ask a Question] {query}", resp))
            if generate_assignment_checked:
                resp = generate_assignment(extracted_text, model)
                st.session_state.conversation_history.insert(0, (f"[Generate Assignment] {query}", resp))
                pdf_bytes = text_to_pdf(resp)
                st.download_button("📅 Download Assignment PDF", pdf_bytes, file_name="assignment.pdf", mime="application/pdf")
            if generate_quiz_checked:
                resp = generate_quiz(extracted_text, model)
                st.session_state.conversation_history.insert(0, (f"[Generate Quiz] {query}", resp))
                quiz_bytes = text_to_pdf(resp)
                st.download_button("📝 Download Quiz PDF", quiz_bytes, file_name="quiz.pdf", mime="application/pdf")

    if st.session_state.conversation_history:
        st.markdown("### 💬 Chat History")
        for user_input, ai_response in st.session_state.conversation_history:
            st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-ai">{ai_response}</div>', unsafe_allow_html=True)

elif not uploaded_file:
    st.info("👈 Please upload a PDF file from the sidebar.")
elif not api_key:
    st.warning("🔒 Please enter your Gemini API key to proceed.")
