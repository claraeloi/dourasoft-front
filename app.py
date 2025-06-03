import streamlit as st
import requests
from markdown import markdown
from pathlib import Path
import base64

# --- Config da página ---
st.set_page_config(page_title="Auto AI", page_icon="logo.png", layout="wide")

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
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            st.markdown(markdown(message["content"]), unsafe_allow_html=True)

# Campo de input
user_input = st.chat_input("Digite sua pergunta...")

# Envia a pergunta
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Consultando..."):
            try:
                response = requests.post(
                    "https://japkihqzmd.execute-api.us-east-1.amazonaws.com/query",
                    json={
                        "question": user_input,
                        "chat_history": st.session_state.chat_history
                    },
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
