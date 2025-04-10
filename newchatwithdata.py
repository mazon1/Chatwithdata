import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PyPDF2 import PdfReader  # For PDF parsing

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

# Function to generate response from the model
def generate_response(prompt, context):
    try:
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        # Include context from uploaded data in the prompt
        response = model.generate_content(f"{prompt}\n\nContext:\n{context}")
        return response.text  # Use 'text' attribute
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process your request."

# Streamlit app
def main():
    st.title("Project-Specific Chatbot")
    st.write("Upload project-related files and ask questions based on the data.")

    # File upload
    uploaded_files = st.file_uploader("Upload your project files (CSV/Excel/PDF)", type=["csv", "xlsx", "pdf"], accept_multiple_files=True)

    # Prepare data context
    data_context = ""
    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                elif file.name.endswith('.xlsx'):
                    df = pd.read_excel(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                elif file.name.endswith('.pdf'):
                    text = extract_text_from_pdf(file)
                    data_context += f"\nExtracted text from {file.name}:\n{text[:1000]}...\n"  # Limit to first 1000 characters
                st.success(f"Successfully processed {file.name}")
            except Exception as e:
                st.error(f"Error processing {file.name}: {e}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.text_input("Ask a question about your project:", key="input")
    if st.button("Send"):
        if user_input and data_context:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            response = generate_response(user_input, data_context)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        elif not data_context:
            st.error("Please upload relevant files to ask project-specific questions.")

    for message in st.session_state.chat_history:
        st.write(f"{message['role'].capitalize()}: {message['content']}")

if __name__ == "__main__":
    main()
