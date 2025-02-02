import streamlit as st
import pandas as pd
import os
import pdfplumber
import pytesseract
from PIL import Image
import docx
from fpdf import FPDF
import google.generativeai as genai
import sqlite3

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", st.secrets.get("GOOGLE_API_KEY"))
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize SQLite Database
conn = sqlite3.connect("uploaded_data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    extracted_text TEXT
)
""")
conn.commit()

# Function to Extract Text from PDFs
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n" if page.extract_text() else ""
    return text if text else "No text found."

# Function to Extract Text from Images
def extract_text_from_image(image_file):
    image = Image.open(image_file)
    return pytesseract.image_to_string(image)

# Function to Extract Text from Word Documents
def extract_text_from_docx(doc_file):
    doc = docx.Document(doc_file)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to Extract Data from Excel Files
def extract_text_from_excel(excel_file):
    df = pd.read_excel(excel_file)
    return df.to_string()

# Function to Generate a Response with Gemini
def generate_response(prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text  
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Unable to process request."

# Function to Populate a Template
def generate_report(template_text, extracted_data):
    report_text = template_text
    for key, value in extracted_data.items():
        report_text = report_text.replace(f"{{{{{key}}}}}", value)  # Replace placeholders
    return report_text

# Function to Export as PDF
def export_to_pdf(report_text, filename="generated_report.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in report_text.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)

    pdf.output(filename)
    return filename

# Streamlit UI
st.title("📄 Multi-File Upload & Automated Report Generation")

# Upload Multiple Documents
uploaded_files = st.file_uploader("Upload multiple documents (PDF, Word, Excel, Image)", 
                                  type=["pdf", "docx", "xlsx", "jpg", "png"], 
                                  accept_multiple_files=True)

extracted_data = {}

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type
        extracted_text = ""

        if "pdf" in file_type:
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif "image" in file_type or "png" in file_type or "jpg" in file_type:
            extracted_text = extract_text_from_image(uploaded_file)
        elif "word" in file_type or "docx" in file_type:
            extracted_text = extract_text_from_docx(uploaded_file)
        elif "excel" in file_type or "xlsx" in file_type:
            extracted_text = extract_text_from_excel(uploaded_file)
        else:
            extracted_text = "Unsupported file format."

        # Save to SQLite database
        cursor.execute("INSERT INTO documents (file_name, extracted_text) VALUES (?, ?)", 
                       (uploaded_file.name, extracted_text))
        conn.commit()

        extracted_data[uploaded_file.name] = extracted_text

    st.success("✅ Documents uploaded and processed!")

# Template Upload & Report Generation
st.header("📑 Generate Report from Template")

template_file = st.file_uploader("Upload a report template (Word or Text file)", type=["docx", "txt"])
if template_file:
    template_text = extract_text_from_docx(template_file) if "docx" in template_file.type else template_file.read().decode()

    st.text_area("📜 Template Preview:", template_text, height=200)

    # Select document data for report
    doc_options = st.selectbox("Select document data to use:", extracted_data.keys() if extracted_data else [])
    
    if doc_options:
        selected_text = extracted_data[doc_options]
        report_text = generate_report(template_text, {"EXTRACTED_DATA": selected_text})

        st.text_area("📄 Generated Report:", report_text, height=300)

        if st.button("Export as PDF"):
            pdf_filename = export_to_pdf(report_text)
            st.success("📂 Report generated successfully!")
            st.download_button("Download Report", open(pdf_filename, "rb"), file_name=pdf_filename, mime="application/pdf")
