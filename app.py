import streamlit as st
import requests
from markdown import markdown

# --- Config da página ---
st.set_page_config(page_title="DouraSoft AI Assistant", page_icon="logo.png", layout="wide")

# --- Estilos customizados ---
st.markdown("""
    <style>
        .css-18e3th9 {
            padding-top: 3rem;
        }
        .block-container {
            max-width: 90%;
            padding-left: 5rem;
            padding-right: 5rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Chat ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Mostra o histórico
for message in st.session_state.chat_history:
    with st.chat_message("user" if message["role"] == "user" else "assistant"):
        st.markdown(message["content"] if message["role"] == "user" else markdown(message["content"]), unsafe_allow_html=True)

# Upload opcional de 1 PDF
uploaded_file = st.file_uploader("Anexar PDF (opcional)", type="pdf", accept_multiple_files=False)
file_name = None

# Campo de input
user_input = st.chat_input("Digite sua pergunta...")

# Envia a pergunta
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    file_info = None
    if uploaded_file:
        try:
            # Solicita signed URL
            signed_url_response = requests.post(
                "https://japkihqzmd.execute-api.us-east-1.amazonaws.com/signed-url",  # ← troque pela sua URL real
                json={"files": [{"filename": uploaded_file.name, "contentType": "application/pdf"}]}
            )
            signed_url_response.raise_for_status()
            signed = signed_url_response.json()["signedUrls"][0]

            # Faz upload do PDF para a signed URL
            upload_response = requests.put(
                signed["url"],
                data=uploaded_file.read(),
                headers={"Content-Type": "application/pdf"}
            )
            upload_response.raise_for_status()

            # Guarda info do arquivo para mandar à API
            file_name = signed["filename"]

        except Exception as e:
            st.error(f"Erro ao fazer upload do PDF: {e}")
            file_name = None

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            try:
                payload = {
                    "question": user_input,
                    "chat_history": st.session_state.chat_history
                }
                if file_name:
                    payload["report_s3_key"] = file_name

                response = requests.post(
                    "https://japkihqzmd.execute-api.us-east-1.amazonaws.com/query",
                    json=payload,
                    timeout=90
                )
                response.raise_for_status()
                resposta = response.json().get("resposta", "Não consegui gerar uma resposta.")
            except requests.exceptions.Timeout:
                resposta = "A consulta demorou demais para responder. Tente novamente."
            except requests.exceptions.RequestException as e:
                resposta = f"Erro ao consultar a API: {e}"

            st.session_state.chat_history.append({"role": "assistant", "content": resposta})
            st.markdown(markdown(resposta.strip()), unsafe_allow_html=True)
