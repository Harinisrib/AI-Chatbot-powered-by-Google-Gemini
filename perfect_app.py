import streamlit as st
import google.generativeai as genai
import os
import re
from datetime import datetime, timedelta
from PIL import Image
import io
import requests
import uuid
try:
    from docx import Document
    DOCX_AVAILABLE = True
except:
    DOCX_AVAILABLE = False

# Backend API URL
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page config
st.set_page_config(
    page_title="Gemini AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# PWA Support - Add manifest and service worker
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/app/static/service-worker.js')
    .then(reg => console.log('Service Worker registered'))
    .catch(err => console.log('Service Worker registration failed'));
}

// Request notification permission
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission();
}
</script>
""", unsafe_allow_html=True)

# Clean dark theme - ChatGPT style
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

.stApp {
    background-color: #212121;
}

section[data-testid="stSidebar"] {
    background-color: #171717;
}

.stChatMessage {
    background-color: transparent;
    padding: 1rem;
}

.stChatMessage[data-testid="user"] {
    background-color: #2f2f2f;
}

h1, h2, h3, p {
    color: #ececec;
}

.stButton button {
    background-color: #2f2f2f;
    color: #ececec;
    border: none;
}

.stButton button:hover {
    background-color: #3f3f3f;
}

/* Full width chat input */
.stChatInputContainer {
    max-width: 100% !important;
}

section[data-testid="stChatInput"] {
    max-width: 100% !important;
}

.main .block-container {
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* Sidebar toggle button visible */
button[kind="header"] {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Gemini AI")

# API
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo')
genai.configure(api_key=API_KEY)

# Session state
if 'chats' not in st.session_state:
    st.session_state.chats = {'chat_1': {'name': 'New Chat', 'messages': []}}
if 'current' not in st.session_state:
    st.session_state.current = 'chat_1'

if 'reminders' not in st.session_state:
    st.session_state.reminders = []

if 'files' not in st.session_state:
    st.session_state.files = []

# User ID (unique per browser)
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

# FCM Token (will be set by JavaScript)
if 'fcm_token' not in st.session_state:
    st.session_state.fcm_token = None

chat = st.session_state.chats[st.session_state.current]

# Chat instance
def get_chat(messages):
    model = genai.GenerativeModel('gemini-2.5-flash',
        system_instruction="If user writes in Tamil (Tanglish), respond in Tamil using English letters only. Never use Tamil script.")
    history = []
    for msg in messages:
        history.append({'role': 'user' if msg['role'] == 'user' else 'model', 'parts': [msg['content']]})
    return model.start_chat(history=history)

if 'instance' not in st.session_state:
    st.session_state.instance = get_chat(chat['messages'])

# Backend API functions
def create_reminder_backend(reminder_time, message="Reminder!"):
    """Send reminder to backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/reminders",
            json={
                "user_id": st.session_state.user_id,
                "reminder_time": reminder_time.isoformat(),
                "message": message,
                "fcm_token": st.session_state.fcm_token
            }
        )
        return response.json()
    except Exception as e:
        print(f"Error creating reminder: {e}")
        return None

def get_reminders_backend():
    """Get reminders from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/reminders/{st.session_state.user_id}")
        return response.json()
    except Exception as e:
        print(f"Error fetching reminders: {e}")
        return []

def delete_reminder_backend(reminder_id):
    """Delete reminder from backend"""
    try:
        requests.delete(f"{BACKEND_URL}/reminders/{reminder_id}")
        return True
    except Exception as e:
        print(f"Error deleting reminder: {e}")
        return False

# Reminder extraction - catches "remind", "reminder", "set", etc.
def extract_reminder(text):
    # Check if it's a reminder request
    if not any(word in text.lower() for word in ['remind', 'reminder', 'set', 'alert']):
        return None
    
    match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)', text.lower())
    if match:
        h, m, p = int(match.group(1)), int(match.group(2)), match.group(3)
        if p == 'pm' and h != 12: h += 12
        if p == 'am' and h == 12: h = 0
        t = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if t < datetime.now(): t += timedelta(days=1)
        return {'time': t}
    return None

# Sidebar
with st.sidebar:
    st.markdown("### 💬 Chats")
    
    if st.button("➕ New Chat", use_container_width=True):
        import time
        new_id = f'chat_{int(time.time())}'
        st.session_state.chats[new_id] = {'name': 'New Chat', 'messages': []}
        st.session_state.current = new_id
        st.session_state.instance = get_chat([])
        st.rerun()
    
    st.divider()
    
    # Reminders with delete
    if st.session_state.reminders:
        st.markdown("**⏰ Reminders**")
        for idx, r in enumerate(st.session_state.reminders):
            mins = int((r['time'] - datetime.now()).total_seconds() // 60)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"📅 {r['time'].strftime('%I:%M %p')} ({mins}m)")
            with col2:
                if st.button("×", key=f"r_{idx}"):
                    st.session_state.reminders.pop(idx)
                    st.rerun()
        st.divider()
    
    # File upload in sidebar
    st.markdown("**📎 Attach Files**")
    uploaded = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'txt', 'docx'], label_visibility="collapsed")
    if uploaded:
        if uploaded.type.startswith('image/'):
            img = Image.open(uploaded)
            st.session_state.files.append({'data': img, 'type': 'image'})
            st.success(f"✓ {uploaded.name}")
        elif uploaded.type == 'application/pdf':
            st.session_state.files.append({'data': uploaded.read(), 'type': 'pdf'})
            st.success(f"✓ {uploaded.name}")
        elif uploaded.type == 'text/plain':
            text = uploaded.read().decode('utf-8')
            st.session_state.files.append({'data': text, 'type': 'text'})
            st.success(f"✓ {uploaded.name}")
        elif DOCX_AVAILABLE and uploaded.name.endswith('.docx'):
            doc = Document(io.BytesIO(uploaded.read()))
            text = '\n'.join([p.text for p in doc.paragraphs])
            st.session_state.files.append({'data': text, 'type': 'docx'})
            st.success(f"✓ {uploaded.name}")
    
    st.divider()
    
    # Chat list
    for cid, cdata in st.session_state.chats.items():
        is_current = cid == st.session_state.current
        col1, col2 = st.columns([4, 1])
        
        with col1:
            if st.button(f"{'📌' if is_current else '💬'} {cdata['name']}", 
                        key=f"c_{cid}", use_container_width=True):
                st.session_state.current = cid
                st.session_state.instance = get_chat(cdata['messages'])
                st.rerun()
        
        with col2:
            # Always show delete, but disable if only 1 chat
            can_delete = len(st.session_state.chats) > 1
            if st.button("🗑️", key=f"d_{cid}", disabled=not can_delete):
                del st.session_state.chats[cid]
                if st.session_state.current == cid:
                    st.session_state.current = list(st.session_state.chats.keys())[0]
                st.rerun()

# Check reminders - at the top before messages
for r in st.session_state.reminders[:]:
    if r['time'] <= datetime.now():
        st.balloons()
        st.toast("🔔 REMINDER TIME!", icon="⏰")
        st.warning("⏰ REMINDER! Time's up!")
        st.session_state.reminders.remove(r)

# Display messages
st.markdown(f"### {chat['name']}")
for msg in chat['messages']:
    with st.chat_message(msg['role']):
        st.markdown(msg['content'])

# Chat input
prompt = st.chat_input("Message Gemini...")

# Handle input
if prompt:
    chat['messages'].append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    
    # Check reminder
    reminder = extract_reminder(prompt)
    if reminder:
        # Save to backend
        result = create_reminder_backend(reminder['time'], f"Reminder: {prompt[:50]}")
        
        if result:
            msg = f"✓ Reminder set for {reminder['time'].strftime('%I:%M %p')} - You'll get notification on all devices!"
        else:
            # Fallback to local storage
            st.session_state.reminders.append(reminder)
            msg = f"✓ Reminder set for {reminder['time'].strftime('%I:%M %p')} (local only)"
        
        chat['messages'].append({'role': 'assistant', 'content': msg})
        with st.chat_message('assistant'):
            st.markdown(msg)
        st.rerun()
    
    # Auto-name
    if len(chat['messages']) == 1:
        chat['name'] = ' '.join(prompt.split()[:4]).capitalize()
    
    # Response
    with st.chat_message('assistant'):
        try:
            parts = [prompt]
            if st.session_state.files:
                for f in st.session_state.files:
                    parts.append(f['data'])
                st.session_state.files = []
            
            response = st.session_state.instance.send_message(parts, stream=True)
            full = ""
            placeholder = st.empty()
            for chunk in response:
                if hasattr(chunk, 'text'):
                    full += chunk.text
                    placeholder.markdown(full)
            
            chat['messages'].append({'role': 'assistant', 'content': full})
        except Exception as e:
            st.error(f"Error: {e}")
