import streamlit as st
import google.generativeai as genai
import faiss
import numpy as np
import pandas as pd
import sqlite3
from sentence_transformers import SentenceTransformer
from docx import Document
from fpdf import FPDF

# Initialize Generative AI Model
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
genai.configure(api_key=GOOGLE_API_KEY)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Database Connection
conn = sqlite3.connect("project_data.db")
cursor = conn.cursor()

# Create Table for Storing Grant Applications (if not exists)
cursor.execute('''
CREATE TABLE IF NOT EXISTS grants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT,
    funding_org TEXT,
    amount_requested TEXT,
    impact TEXT,
    timeline TEXT,
    methodology TEXT,
    eligibility TEXT,
    key_objectives TEXT
)
''')
conn.commit()

# Function to Retrieve Data from Database
def fetch_project_data():
    cursor.execute("SELECT * FROM grants")
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=["ID", "Project Name", "Funding Org", "Amount Requested", "Impact", "Timeline", "Methodology", "Eligibility", "Key Objectives"])

# Function to Generate AI-Powered Report
def generate_report(project_name, funding_org, amount, impact, timeline, methodology, eligibility, objectives):
    prompt = f"""
    Generate a structured grant application report using the following details:
    - **Project Name:** {project_name}
    - **Funding Organization:** {funding_org}
    - **Amount Requested:** {amount}
    - **Impact Summary:** {impact}
    - **Timeline:** {timeline}
    - **Methodology:** {methodology}
    - **Eligibility Criteria:** {eligibility}
    - **Key Objectives:** {objectives}

    The report should be well-structured, professional, and formatted for grant submission.
    """
    response = genai.GenerativeModel('gemini-pro').generate_content(prompt)
    return response.text

# Function to Generate a Word Document
def generate_word_doc(content):
    doc = Document()
    doc.add_paragraph(content)
    file_path = "Grant_Application.docx"
    doc.save(file_path)
    return file_path

# Function to Generate a PDF
def generate_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True, align='L')
    file_path = "Grant_Application.pdf"
    pdf.output(file_path)
    return file_path

# Streamlit UI
def main():
    st.title("AI-Powered Grant Application Generator for Alberta")
    st.write("Retrieve project data, generate structured reports, and download as PDF or Word.")

    # Display Stored Projects
    df = fetch_project_data()
    st.dataframe(df)

    # Select a Project
    project_selected = st.selectbox("Select a project to generate an application:", df["Project Name"])

    # Get Project Data
    project_data = df[df["Project Name"] == project_selected].iloc[0]
    project_name = project_data["Project Name"]
    funding_org = project_data["Funding Org"]
    amount = project_data["Amount Requested"]
    impact = project_data["Impact"]
    timeline = project_data["Timeline"]
    methodology = project_data["Methodology"]
    eligibility = project_data["Eligibility"]
    objectives = project_data["Key Objectives"]

    # Generate Report
    if st.button("Generate Report"):
        report_text = generate_report(project_name, funding_org, amount, impact, timeline, methodology, eligibility, objectives)
        st.write("### Generated Report")
        st.write(report_text)

        # Download Options
        doc_path = generate_word_doc(report_text)
        pdf_path = generate_pdf(report_text)

        with open(doc_path, "rb") as f:
            st.download_button("Download Word Document", f, file_name="Grant_Application.docx")

        with open(pdf_path, "rb") as f:
            st.download_button("Download PDF", f, file_name="Grant_Application.pdf")

if __name__ == "__main__":
    main()
