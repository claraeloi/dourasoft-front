import streamlit as st
import boto3
import os
import hmac
import hashlib
import base64
import time
import requests
from botocore.exceptions import ClientError

# Configurações do Cognito
USER_POOL_ID = "us-east-1_SVzrHovUC"
CLIENT_ID = "1k9b1hmudknp8hemju543sj86n"
CLIENT_SECRET = "du6ta1ifrgfjhajhr2u4aqf170566ib4v3ffmkv6jt7s5qb0g0d"
REGION = "us-east-1"

# Inicializa o cliente do Cognito
client = boto3.client('cognito-idp', region_name=REGION)

# Configuração da página
st.set_page_config(page_title="DouraSoft AI Assistant", page_icon=":robot:", layout="wide")

# Estilos CSS personalizados
st.markdown("""
    <style>
        .css-18e3th9 {
            padding-top: 3rem;
        }
        .block-container {
            max-width: 50%;
            padding-left: 5rem;
            padding-right: 5rem;
        }
        .stButton>button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Função para calcular o Secret Hash
def calculate_secret_hash(email):
    message = email + CLIENT_ID
    dig = hmac.new(
        CLIENT_SECRET.encode('utf-8'),
        msg=message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def sign_up(email, password, nome=None):
    try:
        secret_hash = calculate_secret_hash(email)
        user_attributes = [{'Name': 'email', 'Value': email}]
        
        if nome:
            user_attributes.append({'Name': 'name', 'Value': nome})
            
        response = client.sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            Password=password,
            SecretHash=secret_hash,
            UserAttributes=user_attributes
        )
        return True, "Usuário cadastrado com sucesso! Verifique seu email para confirmar a conta."
    except ClientError as e:
        return False, e.response['Error']['Message']

def confirm_sign_up(email, confirmation_code):
    try:
        secret_hash = calculate_secret_hash(email)
        response = client.confirm_sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code,
            SecretHash=secret_hash
        )
        return True, "Conta confirmada com sucesso!"
    except ClientError as e:
        return False, e.response['Error']['Message']

def sign_in(email, password):
    try:
        secret_hash = calculate_secret_hash(email)
        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            }
        )
        
        if 'AuthenticationResult' in response:
            access_token = response['AuthenticationResult']['AccessToken']
            id_token = response['AuthenticationResult']['IdToken']
            refresh_token = response['AuthenticationResult']['RefreshToken']
            
            user_info = client.get_user(AccessToken=access_token)
            user_attributes = {attr['Name']: attr['Value'] for attr in user_info['UserAttributes']}
            
            return True, {
                'email': email,
                'name': user_attributes.get('name'),
                'access_token': access_token,
                'id_token': id_token,
                'refresh_token': refresh_token
            }
        else:
            return False, "Falha na autenticação"
            
    except ClientError as e:
        return False, e.response['Error']['Message']

def forgot_password(email):
    try:
        secret_hash = calculate_secret_hash(email)
        response = client.forgot_password(
            ClientId=CLIENT_ID,
            Username=email,
            SecretHash=secret_hash
        )
        return True, "Código de redefinição enviado para seu email."
    except ClientError as e:
        return False, e.response['Error']['Message']

def confirm_forgot_password(email, confirmation_code, new_password):
    try:
        secret_hash = calculate_secret_hash(email)
        response = client.confirm_forgot_password(
            ClientId=CLIENT_ID,
            Username=email,
            ConfirmationCode=confirmation_code,
            Password=new_password,
            SecretHash=secret_hash
        )
        return True, "Senha redefinida com sucesso!"
    except ClientError as e:
        return False, e.response['Error']['Message']

# Estado da sessão
if 'auth' not in st.session_state:
    st.session_state.auth = None
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'signup_email' not in st.session_state:
    st.session_state.signup_email = ''

# Páginas de autenticação
if st.session_state.auth is None:
    # Página de Login
    if st.session_state.page == 'login':
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.title("Login")
            
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Entrar"):
                    success, result = sign_in(email, password)
                    if success:
                        st.session_state.auth = result
                        st.rerun()
                    else:
                        st.error(f"Erro no login: {result}")
            
            with col2:
                if st.button("Cadastrar"):
                    st.session_state.page = 'signup'
                    st.rerun()
            
            if st.button("Esqueci minha senha"):
                st.session_state.page = 'forgot_password'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Página de Cadastro
    elif st.session_state.page == 'signup':
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.title("Cadastro")
            
            email = st.text_input("Email")
            nome = st.text_input("Nome (opcional)")
            password = st.text_input("Senha", type="password")
            confirm_password = st.text_input("Confirmar Senha", type="password")
            
            if st.button("Cadastrar"):
                if password != confirm_password:
                    st.error("As senhas não coincidem!")
                else:
                    success, result = sign_up(email, password, nome)
                    if success:
                        st.session_state.signup_email = email
                        st.session_state.page = 'confirm_signup'
                        st.rerun()
                        st.success(result)
                    else:
                        st.error(f"Erro no cadastro: {result}")
            
            if st.button("Voltar para Login"):
                st.session_state.page = 'login'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Página de Confirmação de Cadastro
    elif st.session_state.page == 'confirm_signup':
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.title("Confirmar Cadastro")
            st.write(f"Enviamos um código de confirmação para {st.session_state.signup_email}")
            
            confirmation_code = st.text_input("Código de Confirmação")
            
            if st.button("Confirmar"):
                success, result = confirm_sign_up(st.session_state.signup_email, confirmation_code)
                if success:
                    st.success(result)
                    st.session_state.page = 'login'
                    st.rerun()
                else:
                    st.error(f"Erro na confirmação: {result}")
            
            if st.button("Reenviar Código"):
                st.info("Código reenviado (implementação pendente)")
            
            if st.button("Voltar para Login"):
                st.session_state.page = 'login'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Página de Esqueci a Senha
    elif st.session_state.page == 'forgot_password':
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.title("Redefinir Senha")
            
            email = st.text_input("Email")
            
            if st.button("Enviar Código"):
                success, result = forgot_password(email)
                if success:
                    st.session_state.reset_email = email
                    st.session_state.page = 'confirm_forgot_password'
                    st.rerun()
                    st.success(result)
                else:
                    st.error(f"Erro: {result}")
            
            if st.button("Voltar para Login"):
                st.session_state.page = 'login'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Página de Confirmação de Redefinição de Senha
    elif st.session_state.page == 'confirm_forgot_password':
        with st.container():
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.title("Confirmar Redefinição")
            st.write(f"Enviamos um código para redefinir a senha de {st.session_state.reset_email}")
            
            confirmation_code = st.text_input("Código de Confirmação")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.button("Redefinir Senha"):
                if new_password != confirm_password:
                    st.error("As senhas não coincidem!")
                else:
                    success, result = confirm_forgot_password(
                        st.session_state.reset_email,
                        confirmation_code,
                        new_password
                    )
                    if success:
                        st.success(result)
                        st.session_state.page = 'login'
                        st.rerun()
                    else:
                        st.error(f"Erro: {result}")
            
            if st.button("Voltar para Login"):
                st.session_state.page = 'login'
                st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

# Se o usuário estiver autenticado, mostra o aplicativo principal
else:
    # Barra lateral com informações do usuário e logout
    with st.sidebar:
        st.write(f"Bem-vindo, {st.session_state.auth.get('name', st.session_state.auth['email'])}!")
        st.write(f"Email: {st.session_state.auth['email']}")
        if st.button("Logout"):
            st.session_state.auth = None
            st.rerun()
    
    # Restante do seu aplicativo Streamlit...
    st.title("DouraSoft AI Assistant")
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message("user" if message["role"] == "user" else "assistant"):
            st.markdown(message["content"] if message["role"] == "user" else message["content"], unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Anexar arquivo (PDF ou CSV)", type=["pdf", "csv"], accept_multiple_files=False)
    file_name = None
    content_type = None

    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            content_type = "application/pdf"
        elif uploaded_file.type == "text/csv" or uploaded_file.name.endswith(".csv"):
            content_type = "text/csv"
        else:
            st.error("Tipo de arquivo não suportado.")
            uploaded_file = None

    user_input = st.chat_input("Digite sua pergunta...")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)

        if uploaded_file and content_type:
            try:
                headers = {
                    "Authorization": f"Bearer {st.session_state.auth['access_token']}"
                }
                
                signed_url_response = requests.post(
                    "https://japkihqzmd.execute-api.us-east-1.amazonaws.com/signed-url",
                    json={"files": [{"filename": uploaded_file.name, "contentType": content_type}]},
                    headers=headers
                )
                signed_url_response.raise_for_status()
                signed = signed_url_response.json()["signedUrls"][0]

                upload_response = requests.put(
                    signed["url"],
                    data=uploaded_file.read(),
                    headers={"Content-Type": content_type}
                )
                upload_response.raise_for_status()
                file_name = signed["filename"]

            except Exception as e:
                st.error(f"Erro ao fazer upload do arquivo: {e}")
                file_name = None

        with st.chat_message("assistant"):
            with st.spinner("Enviando sua consulta..."):
                try:
                    payload = {
                        "question": user_input,
                        "chat_history": st.session_state.chat_history
                    }
                    if file_name:
                        payload["report_s3_key"] = file_name

                    headers = {
                        "Authorization": f"Bearer {st.session_state.auth['access_token']}"
                    }
                    
                    response = requests.post(
                        "https://japkihqzmd.execute-api.us-east-1.amazonaws.com/process",
                        json=payload,
                        timeout=30,
                        headers=headers
                    )
                    response.raise_for_status()
                    task_id = response.json().get("taskId")

                    if not task_id:
                        raise ValueError("A resposta não retornou um task_id válido.")

                    st.success("Pergunta enviada com sucesso! Buscando resposta...")

                    resposta = None
                    polling_url = f"https://japkihqzmd.execute-api.us-east-1.amazonaws.com/result/{task_id}"
                    polling_timeout = 150
                    polling_interval = 5
                    start_time = time.time()

                    while time.time() - start_time < polling_timeout:
                        poll_response = requests.get(polling_url, timeout=10, headers=headers)
                        poll_response.raise_for_status()
                        data = poll_response.json()

                        if data.get("status") == "FAILED":
                            st.error(f"Houve um erro ao processar a consulta. Por favor, tente novamente.")
                            break

                        if data.get("status") == "FINISHED":
                            resposta = data.get("result")
                            break

                        time.sleep(polling_interval)

                    if not resposta:
                        resposta = "A consulta está demorando mais que o esperado. Sua pergunta foi enviada e será processada em breve."

                except Exception as e:
                    resposta = f"Erro ao processar consulta: {e}"

                st.session_state.chat_history.append({"role": "assistant", "content": resposta})
                st.markdown(resposta.strip(), unsafe_allow_html=True)