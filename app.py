import streamlit as st
import google.generativeai as genai
import os

# Page config
st.set_page_config(
    page_title="Gemini Chatbot",
    page_icon="🤖",
    layout="centered"
)

# Custom CSS for black theme
st.markdown("""
    <style>
    .stApp {
        background-color: #0e0e0e;
    }
    .stChatMessage {
        background-color: #1a1a1a;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 1px solid #333333;
    }
    h1 {
        color: #ffffff;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Gemini Chatbot")

# Configure API
try:
    # Try to get from Streamlit secrets first (for cloud deployment)
    API_KEY = st.secrets.get("GEMINI_API_KEY", os.getenv('GEMINI_API_KEY', 'AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo'))
except:
    API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo')
genai.configure(api_key=API_KEY)

# Initialize session state
if 'chat_sessions' not in st.session_state:
    st.session_state.chat_sessions = {}
if 'current_chat_id' not in st.session_state:
    st.session_state.current_chat_id = 'chat_1'
    st.session_state.chat_sessions['chat_1'] = {
        'name': 'New Chat',
        'messages': []
    }

# Get current chat
current_chat = st.session_state.chat_sessions[st.session_state.current_chat_id]

# Recreate chat object from history
def get_chat_instance(messages):
    model = genai.GenerativeModel('gemini-2.5-flash')
    history = []
    for msg in messages:
        role = 'user' if msg['role'] == 'user' else 'model'
        history.append({'role': role, 'parts': [msg['content']]})
    return model.start_chat(history=history)

if 'chat_instance' not in st.session_state:
    st.session_state.chat_instance = get_chat_instance(current_chat['messages'])

# Display current chat name
st.caption(f"💬 {current_chat['name']}")

# Display chat messages
for message in current_chat['messages']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    current_chat['messages'].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Auto-generate chat name from first message
    if len(current_chat['messages']) == 1:
        # Extract key words from first message (first 3-4 words or 30 chars)
        words = prompt.split()[:4]
        chat_name = ' '.join(words)
        if len(chat_name) > 30:
            chat_name = chat_name[:30] + "..."
        current_chat['name'] = chat_name.capitalize()
    
    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = st.session_state.chat_instance.send_message(prompt)
                st.markdown(response.text)
                current_chat['messages'].append({"role": "assistant", "content": response.text})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                current_chat['messages'].append({"role": "assistant", "content": error_msg})

# Sidebar
with st.sidebar:
    st.header("Chat Sessions")
    
    if st.button("➕ New Chat", use_container_width=True):
        # Create new chat
        import time
        new_chat_id = f'chat_{int(time.time())}'
        st.session_state.chat_sessions[new_chat_id] = {
            'name': 'New Chat',
            'messages': []
        }
        st.session_state.current_chat_id = new_chat_id
        st.session_state.chat_instance = get_chat_instance([])
        st.rerun()
    
    st.divider()
    
    # Display all chat sessions
    for chat_id, chat_data in st.session_state.chat_sessions.items():
        msg_count = len(chat_data['messages'])
        is_current = chat_id == st.session_state.current_chat_id
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button(
                f"{'📌' if is_current else '💬'} {chat_data['name']} ({msg_count})",
                key=f"btn_{chat_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_instance = get_chat_instance(chat_data['messages'])
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"del_{chat_id}", disabled=len(st.session_state.chat_sessions) == 1):
                del st.session_state.chat_sessions[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.current_chat_id = list(st.session_state.chat_sessions.keys())[0]
                st.rerun()
