import streamlit as st
import PyPDF2
import google.generativeai as genai
import re
from fpdf import FPDF

# ====== BACKGROUND AND STYLING ======
def set_bg_image():
    st.markdown(
        """
         <style>
        
        /* All text in the main area */
        .stMarkdown p, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        .stText, .stHeading, .stSubheader, .stCaption {
            color: black !important;
        }
        /* Make Gemini API Key input text blue */
section[data-testid="stSidebar"] input[type="password"] {
    color: #1E90FF !important;  /* Permanent Blue */
}

        /* Keep original background styles */
        .stApp {
            background-image: url("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQgYCf7zQFjCI8WO8Y5XFuGpes5GuCXbyIQEA&s");
            background-size: cover;
            background-attachment: fixed;
            background-repeat: no-repeat;
            background-position: center;
        }

        /* Keep original container styles */
        .block-container {
            background-color: rgba(255, 255, 255, 0.85);
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
        }

        /* UPDATED UPLOAD BOX STYLING - Changed to match space theme */
        div[data-testid="stFileUploader"] {
            background: linear-gradient(135deg, rgba(13, 27, 42, 0.9), rgba(27, 38, 59, 0.8)) !important;
            border: 2px dashed rgba(100, 149, 237, 0.6) !important;
            border-radius: 12px !important;
            padding: 25px !important;
            transition: all 0.3s ease !important;
            margin-bottom: 20px !important;
            backdrop-filter: blur(10px) !important;
        }

        div[data-testid="stFileUploader"]:hover {
            border-color: rgba(135, 206, 250, 0.8) !important;
            background: linear-gradient(135deg, rgba(13, 27, 42, 0.95), rgba(27, 38, 59, 0.85)) !important;
            box-shadow: 0 8px 25px rgba(100, 149, 237, 0.3) !important;
            transform: translateY(-2px) !important;
        }

        /* Target all inner elements of file uploader */
        div[data-testid="stFileUploader"] * {
            background-color: transparent !important;
        }

        /* Specific targeting for the white drag area */
        div[data-testid="stFileUploader"] > section {
            background: transparent !important;
        }

        div[data-testid="stFileUploader"] > section > div {
            background: rgba(13, 27, 42, 0.3) !important;
            border-radius: 8px !important;
            border: 1px dashed rgba(100, 149, 237, 0.4) !important;
        }

        div[data-testid="stFileUploader"] > section > div > div {
            background: transparent !important;
        }

        /* Upload button styling */
        div[data-testid="stFileUploader"] > section > div > div > button {
            background: linear-gradient(135deg, #4a6fa5, #5a7fb5) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(74, 111, 165, 0.4) !important;
        }

        div[data-testid="stFileUploader"] > section > div > div > button:hover {
            background: linear-gradient(135deg, #3a56b1, #4a66c1) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(74, 111, 165, 0.6) !important;
        }

        /* Text styling */
        div[data-testid="stFileUploader"] > label > p {
            color: rgba(255, 255, 255, 0.95) !important;
            font-weight: 600 !important;
            font-size: 16px !important;
            margin-bottom: 15px !important;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5) !important;
        }

        div[data-testid="stFileUploader"] > section > div > div > div > small {
            color: rgba(255, 255, 255, 0.8) !important;
            font-size: 13px !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
        }

        /* Style all text elements inside uploader */
        div[data-testid="stFileUploader"] > section > div > div > div,
        div[data-testid="stFileUploader"] > section > div > div > div > div,
        div[data-testid="stFileUploader"] span,
        div[data-testid="stFileUploader"] p {
            color: rgba(255, 255, 255, 0.9) !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5) !important;
        }

        /* Keep all other original styles below */
        section[data-testid="stSidebar"] {
            background-color: #001f3f !important;
        }
        section[data-testid="stSidebar"] * {
            color: white !important;
        }
        .stDownloadButton {
            margin-top: 1rem;
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
            word-wrap: break-word;
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
            word-wrap: break-word;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
set_bg_image()

# ====== TEXT PROCESSING ======
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text.strip()

def clean_response(text):
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    return cleaned.strip()

def detect_topics(text):
    lines = text.splitlines()
    candidates = []
    for line in lines:
        line = line.strip()
        if len(line) > 5 and (
            line.isupper() or 
            line.istitle() or 
            re.match(r'^\d+(\.\d+)*\s+[A-Za-z]', line)
        ):
            candidates.append(line)
    topics = list(set([re.sub(r'^\d+(\.\d+)*\s*', '', t) for t in candidates if len(t.split()) <= 8]))
    return sorted(topics)

# ====== GEMINI FUNCTIONS ======
def generate_quiz(text, model, topic=None):
    prompt = f"""
    You are an experienced academic instructor.

    Based on the following semester outline, create a set of **5 multiple-choice questions** on the topic "{topic}".

    - Each question should have four answer options labeled A to D.
    - Clearly indicate the correct answer at the end of each question.
    - Ensure the questions are relevant to the topic and consistent with the outline.

    Semester Outline:
    {text}
    """
    response = model.generate_content(prompt)
    return clean_response(response.text)

def generate_assignment(text, model, topic):
    prompt = f"""
    Create a university-level assignment on the topic "{topic}" using this outline.
    Include title, intro, objectives, task details, and guidelines.
    \n\nOutline:\n{text}
    """
    response = model.generate_content(prompt)
    return clean_response(response.text)
def ask_question(text, query, model):
    prompt = f"""
You are a knowledgeable and friendly academic assistant. Your job is to answer students' questions based on the provided semester outline.

Use the outline below to inform your response. Aim for clarity, helpfulness, and structure. If the answer is not found directly in the outline, use general academic knowledge to assist, but state that you're extrapolating beyond the document.

Semester Outline:
{text}

User Query:
{query}

Please respond as if you're chatting with a university student. Use:
- Bullet points for lists
- Paragraphs for explanations
- Headings for structure if needed

Always maintain a helpful and polite tone.
"""
    response = model.generate_content(prompt)
    return clean_response(response.text)


# ====== PDF CREATION ======
def text_to_pdf(text):
    replacements = {
        '\u2013': '-', '\u2014': '-', '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2022': '*', '\u00a0': ' '
    }
    for unicode_char, ascii_char in replacements.items():
        text = text.replace(unicode_char, ascii_char)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    return pdf.output(dest='S').encode('latin1', errors='ignore')

# ====== SIDEBAR ======
st.sidebar.title("🗭 Semester Controls")
api_key = st.sidebar.text_input("🔑 Enter your Gemini API Key", type="password")
uploaded_file = st.sidebar.file_uploader("📄 Upload Semester Outline (PDF)", type=["pdf"])

st.sidebar.markdown("🚀 **Select Action(s)**")
ask_question_checked = st.sidebar.checkbox("Ask a Question")
generate_assignment_checked = st.sidebar.checkbox("Generate Assignment")
generate_quiz_checked = st.sidebar.checkbox("Generate Quiz")

# ====== MAIN PAGE ======
st.title("📘 Semester Assistant (Gemini AI)")
st.write("Interact with your uploaded semester outline using AI-powered Q&A, assignments, and quizzes.")

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if uploaded_file and api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if "outline_text" not in st.session_state or not st.session_state.outline_text:
        with st.spinner("🔍 Extracting text from uploaded file..."):
            text = extract_text_from_pdf(uploaded_file)
            st.session_state.outline_text = text
            st.session_state.detected_topics = detect_topics(text)
        st.success("✅ Outline processed and topics detected!")

    tab1, tab2 = st.tabs(["📘 Topic-Based Tasks", "🧠 Custom Queries"])

    with tab1:
        detected_topics = st.session_state.detected_topics
        topic = st.selectbox("📚 Choose a topic", detected_topics + ["Enter custom topic..."])
        if topic == "Enter custom topic...":
            topic = st.text_input("✏️ Enter your custom topic", key="custom_topic_input").strip()

        run_button = st.button("🚀 Generate Content", key="run_button")
        if topic and run_button:
            with st.spinner("💬 Getting response from Gemini..."):
                if ask_question_checked:
                    response = ask_question(st.session_state.outline_text, topic, model)
                    st.session_state.conversation_history.insert(0, (f"[Ask a Question] {topic}", response))

                if generate_assignment_checked:
                    assignment = generate_assignment(st.session_state.outline_text, model, topic)
                    st.session_state.conversation_history.insert(0, (f"[Assignment] {topic}", assignment))
                    pdf_bytes = text_to_pdf(assignment)
                    st.download_button("📅 Download Assignment PDF", pdf_bytes, file_name="assignment.pdf", mime="application/pdf")

                if generate_quiz_checked:
                    quiz = generate_quiz(st.session_state.outline_text, model, topic)
                    st.session_state.conversation_history.insert(0, (f"[Quiz] {topic}", quiz))
                    pdf_bytes = text_to_pdf(quiz)
                    st.download_button("📅 Download Quiz PDF", pdf_bytes, file_name="quiz.pdf", mime="application/pdf")

    with tab2:
        user_query = st.text_input("💬 Ask a custom query about the outline", key="custom_query_input")
        if user_query.strip() and st.button("🔍 Submit Query"):
            with st.spinner("💡 Generating answer to your query..."):
                custom_response = ask_question(st.session_state.outline_text, user_query.strip(), model)
                st.session_state.conversation_history.insert(0, (f"[Custom Query] {user_query.strip()}", custom_response))

    if st.session_state.conversation_history:
        st.markdown("### 💬 Chat History")
        for user_input, ai_response in st.session_state.conversation_history:
            st.markdown(f'<div class="chat-bubble-user">{user_input}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-ai">{ai_response}</div>', unsafe_allow_html=True)

elif not uploaded_file:
    st.info("👈 Please upload a PDF file from the sidebar.")
elif not api_key:
    st.warning("🔐 Please enter your Gemini API key to proceed.")
