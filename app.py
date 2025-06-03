import streamlit as st
import requests
from markdown import markdown

# --- Config da página ---
st.set_page_config(page_title="Auto AI", page_icon="🤖", layout="wide")

# --- Estilos customizados ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            max-width: 800px;
            margin: auto;
        }
        .chat-message {
            display: flex;
            align-items: flex-start;
            gap: 1rem;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .chat-message.user {
            background-color: #e0f7fa;
        }
        .chat-message.assistant {
            background-color: #f1f8e9;
        }
        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-color: #ccc;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        .content {
            flex: 1;
        }
        h1 {
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Título ---
st.markdown("## 🤖 Auto AI - Assistente Inteligente")

# --- Estado do chat ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Exibição do histórico de chat ---
for message in st.session_state.chat_history:
    role = message["role"]
    avatar_label = "👤" if role == "user" else "🤖"
    message_class = "user" if role == "user" else "assistant"

    st.markdown(f"""
        <div class="chat-message {message_class}">
            <div class="avatar">{avatar_label}</div>
            <div class="content">{markdown(message['content'])}</div>
        </div>
    """, unsafe_allow_html=True)

# --- Campo de input ---
user_input = st.chat_input("Digite sua pergunta...")

# --- Envio da pergunta ---
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

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
            resposta = "⏱️ A consulta demorou demais para responder. Tente novamente."
        except requests.exceptions.RequestException as e:
            resposta = f"❌ Erro ao consultar a API: {e}"

    st.session_state.chat_history.append({"role": "assistant", "content": resposta})
    st.rerun()