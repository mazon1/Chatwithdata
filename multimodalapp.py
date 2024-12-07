import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PyPDF2 import PdfReader  # For PDF parsing
from PIL import Image
import pytesseract  # For OCR
import pandasql as ps  # For SQL queries on DataFrames

# Set up the API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', st.secrets.get("GOOGLE_API_KEY"))
genai.configure(api_key=GOOGLE_API_KEY)

# Function to extract text from PDF
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
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return ""

# Function to generate response from the model
def generate_response(prompt, context):
    try:
        model = genai.GenerativeModel('gemini-pro')
        # Include context from uploaded data in the prompt
        response = model.generate_content(f"{prompt}\n\nContext:\n{context}")
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process your request."

# Streamlit app
def main():
    st.title("Multimodal Data Query Application")
    st.write("Upload project-related files, including images, CSVs, PDFs, or screenshots. Ask questions or run SQL queries.")

    # File upload
    uploaded_files = st.file_uploader("Upload your project files (CSV/Excel/PDF/Images)", type=["csv", "xlsx", "pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

    # Prepare data context
    data_context = ""
    dataframes = {}  # To store uploaded DataFrames for SQL queries
    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                    dataframes[file.name] = df
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                    dataframes[file.name] = df
                elif file.name.endswith('.pdf'):
                    text = extract_text_from_pdf(file)
                    data_context += f"\nExtracted text from {file.name}:\n{text[:1000]}...\n"  # Limit to first 1000 characters
                elif file.name.endswith(('png', 'jpg', 'jpeg')):
                    text = extract_text_from_image(file)
                    data_context += f"\nExtracted text from {file.name}:\n{text[:1000]}...\n"  # Limit to first 1000 characters
                st.success(f"Successfully processed {file.name}")
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # User input type
    user_query_type = st.radio("What type of query would you like to perform?", ("Natural Language", "SQL Query"))

    if user_query_type == "Natural Language":
        user_input = st.text_input("Ask a question about your project:", key="input_nl")
        if st.button("Send Natural Language Query"):
            if user_input and data_context:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                response = generate_response(user_input, data_context)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            elif not data_context:
                st.error("Please upload relevant files to ask project-specific questions.")

    elif user_query_type == "SQL Query":
        st.write("Available DataFrames:")
        for idx, name in enumerate(dataframes.keys()):
            st.write(f"{idx+1}: {name}")

        sql_query = st.text_area("Enter your SQL query (use the DataFrame name as a table):", key="input_sql")
        selected_df = st.selectbox("Select the DataFrame to query:", list(dataframes.keys()))
        if st.button("Run SQL Query"):
            if sql_query and selected_df in dataframes:
                try:
                    result = ps.sqldf(sql_query, locals())
                    st.write("Query Result:")
                    st.dataframe(result)
                except Exception as e:
                    st.error(f"Error in SQL query: {e}")
            else:
                st.error("Please select a DataFrame and enter a valid SQL query.")

    # Display chat history
    for message in st.session_state.chat_history:
        st.write(f"{message['role'].capitalize()}: {message['content']}")

if __name__ == "__main__":
    main()
