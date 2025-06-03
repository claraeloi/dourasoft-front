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
        .logout-button {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 9999;
        }
        .logout-button button {
            background-color: #f63366;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 13px;
            cursor: pointer;
        }
        .block-container {
            max-width: 90%;
            padding-left: 5rem;
            padding-right: 5rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Autenticação simples ---
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# if not st.session_state.authenticated:
    # Logo centralizada com "Login"
    # logo_path = Path("logo.png")
    # logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()

    # st.markdown(f"""
    #     <div style="text-align: center; margin-top: 4rem; margin-bottom: 2rem;">
    #         <img src="data:image/png;base64,{logo_base64}" width="100">
    #         <h2 style="color: white; margin-top: 1rem;">Login</h2>
    #     </div>
    # """, unsafe_allow_html=True)

    # username = st.text_input("Usuário")
    # password = st.text_input("Senha", type="password")
    # if st.button("Entrar"):
    #     if username == "admin" and password == "4dm1n!A":
    #         st.session_state.authenticated = True
    #         st.rerun()
    #     else:
    #         st.error("Credenciais inválidas.")
    # st.stop()

# --- Botão de Logout ---
# logout_placeholder = st.empty()
# with logout_placeholder.container():
#     if st.button("🔓 Logout"):
#         for key in list(st.session_state.keys()):
#             del st.session_state[key]
#         st.rerun()

# --- Logo e Título Centralizados ---
# logo_path = Path("logo.png")
# logo_base64 = base64.b64encode(logo_path.read_bytes()).decode()
# st.markdown(f"""
#     <div style="text-align: center; margin-top: 2rem; margin-bottom: 2rem;">
#         <img src="data:image/png;base64,{logo_base64}" width="120">
#         <h1 style="color: white; margin-top: 1rem;">Assistente Auto AI</h1>
#     </div>
# """, unsafe_allow_html=True)

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
                    "https://xbofyqkdl8.execute-api.us-east-1.amazonaws.com/default/query",
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
