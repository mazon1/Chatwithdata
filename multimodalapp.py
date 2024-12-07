import streamlit as st
import pandas as pd
from PIL import Image
import pytesseract  # For OCR
from PyPDF2 import PdfReader  # For PDF parsing
import pandasql as ps  # For SQL queries on DataFrames
import os
import google.generativeai as genai

# Set up the API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', st.secrets.get("GOOGLE_API_KEY"))
genai.configure(api_key=GOOGLE_API_KEY)

# Function to extract text from PDFs
def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Function to extract text from images using OCR
def extract_text_from_image(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image, config='--psm 6')
        return text.strip()
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

# Function to parse attendance data from OCR output
def parse_attendance_data(text):
    try:
        # Split lines and find rows that contain meaningful data
        lines = text.split('\n')
        rows = []
        for line in lines:
            if any(char.isdigit() for char in line):
                rows.append(line.split())
        
        # Convert rows to DataFrame
        df = pd.DataFrame(rows)
        return df
    except Exception as e:
        st.error(f"Error parsing attendance data: {e}")
        return pd.DataFrame()

# Function to generate a response from generative AI
def generate_response(prompt, context):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"{prompt}\n\nContext:\n{context}")
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process your request."

# Streamlit app
def main():
    st.title("Multimodal Data Query Application")
    st.write("Upload project files of any type (CSV, Excel, PDFs, images, or text files) to process and analyze them.")

    # File upload
    uploaded_files = st.file_uploader("Upload files", type=["csv", "xlsx", "pdf", "png", "jpg", "jpeg", "txt"], accept_multiple_files=True)

    data_context = ""
    dataframes = {}

    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                    st.write(f"**Preview of {file.name}:**")
                    st.dataframe(df.head())
                    dataframes[file.name] = df

                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    st.write(f"**Preview of {file.name}:**")
                    st.dataframe(df.head())
                    dataframes[file.name] = df

                elif file.name.endswith('.pdf'):
                    text = extract_text_from_pdf(file)
                    st.write(f"**Extracted text from {file.name}:**")
                    st.text(text[:1000])
                    data_context += text

                elif file.name.endswith(('png', 'jpg', 'jpeg')):
                    text = extract_text_from_image(file)
                    st.write(f"**Extracted text from {file.name}:**")
                    st.text(text[:1000])
                    df = parse_attendance_data(text)
                    if not df.empty:
                        st.write(f"**Parsed attendance data from {file.name}:**")
                        st.dataframe(df.head())
                        dataframes[file.name] = df

                elif file.name.endswith('.txt'):
                    text = file.read().decode('utf-8')
                    st.write(f"**Extracted text from {file.name}:**")
                    st.text(text[:1000])
                    data_context += text

                st.success(f"Successfully processed {file.name}")
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

    # Query Section
    user_query_type = st.radio("Choose query type:", ("Natural Language", "SQL Query"))

    if user_query_type == "Natural Language":
        user_input = st.text_input("Ask a question about your data:")
        if st.button("Send Natural Language Query"):
            if user_input and data_context:
                response = generate_response(user_input, data_context)
                st.write("**Response:**")
                st.write(response)
            else:
                st.error("Please upload data files and enter a valid query.")

    elif user_query_type == "SQL Query":
        selected_df = st.selectbox("Select a DataFrame to query:", list(dataframes.keys()))
        sql_query = st.text_area("Enter SQL query:")

        if st.button("Run SQL Query"):
            if sql_query and selected_df in dataframes:
                try:
                    df = dataframes[selected_df]
                    result = ps.sqldf(sql_query, locals())
                    st.write("**Query Result:**")
                    st.dataframe(result)
                except Exception as e:
                    st.error(f"Error executing query: {e}")

if __name__ == "__main__":
    main()
