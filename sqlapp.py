import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from PyPDF2 import PdfReader
import pandasql as ps

# Set up the API key
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', st.secrets.get("GOOGLE_API_KEY"))
genai.configure(api_key=GOOGLE_API_KEY)

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# Initialize chat session globally
@st.cache_resource(show_spinner=False)
def get_chat_model():
    model = genai.GenerativeModel("models/gemini-pro")
    return model.start_chat()

# Generate response from Gemini
def generate_response(prompt, context):
    try:
        chat = get_chat_model()
        full_prompt = f"{prompt}\n\nContext:\n{context}"
        response = chat.send_message(full_prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I couldn't process your request."

# Main App
def main():
    st.title("📊 Project Assistant with Gemini-Pro + SQL")
    st.write("Upload project files (CSV, Excel, or PDF) and ask questions using natural language or SQL.")

    uploaded_files = st.file_uploader("Upload your project files", type=["csv", "xlsx", "pdf"], accept_multiple_files=True)

    data_context = ""
    dataframes = {}

    if uploaded_files:
        for file in uploaded_files:
            try:
                if file.name.endswith(".csv"):
                    df = pd.read_csv(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                    dataframes[file.name] = df
                elif file.name.endswith(".xlsx"):
                    df = pd.read_excel(file)
                    data_context += f"\nData from {file.name}:\n{df.head(5).to_string()}\n"
                    dataframes[file.name] = df
                elif file.name.endswith(".pdf"):
                    text = extract_text_from_pdf(file)
                    data_context += f"\nExtracted text from {file.name}:\n{text[:1000]}...\n"
                st.success(f"✅ Processed {file.name}")
            except Exception as e:
                st.error(f"❌ Error processing {file.name}: {e}")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.markdown("---")
    query_type = st.radio("Choose query type:", ("💬 Natural Language", "🧮 SQL Query"))

    if query_type == "💬 Natural Language":
        user_input = st.text_input("Ask a question about your project:", key="nl_input")
        if st.button("Ask Gemini"):
            if user_input and data_context:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                response = generate_response(user_input, data_context)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
            elif not data_context:
                st.warning("Please upload project files first.")

    elif query_type == "🧮 SQL Query":
        if not dataframes:
            st.warning("Please upload a CSV or Excel file first.")
        else:
            selected_df = st.selectbox("Select DataFrame to query:", list(dataframes.keys()))
            sql_query = st.text_area("Write your SQL query below. Use the DataFrame name as the table name.")
            if st.button("Run SQL"):
                try:
                    df = dataframes[selected_df]
                    locals()[selected_df] = df  # Register table name for pandasql
                    result = ps.sqldf(sql_query, locals())
                    st.dataframe(result)
                except Exception as e:
                    st.error(f"SQL Error: {e}")

    # Display chat history
    for msg in st.session_state.chat_history:
        st.markdown(f"**{msg['role'].capitalize()}**: {msg['content']}")

if __name__ == "__main__":
    main()
