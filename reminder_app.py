import streamlit as st
import google.generativeai as genai
import os
import re
from datetime import datetime, timedelta
import json
from PIL import Image
import io

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
    .reminder-box {
        background-color: #1a1a1a;
        border-left: 4px solid #4CAF50;
        padding: 10px;
        margin: 10px 0;
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.title("🤖 Gemini Chatbot with Reminders")

# Configure API
API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCYBRWotxZxE1pQsKFHjUZ8fnhG34DI_oo')
if not API_KEY or API_KEY == '':
    st.error("⚠️ GEMINI_API_KEY not found!")
    st.stop()
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
if 'reminders' not in st.session_state:
    st.session_state.reminders = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

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

# Extract reminder from text
def extract_reminder(text):
    patterns = [
        r'remind me (?:at |about )?(.+?)(?:at |@)(\d{1,2}):?(\d{2})?\s*(am|pm)?',
        r'reminder (?:at |for )?(.+?)(?:at |@)(\d{1,2}):?(\d{2})?\s*(am|pm)?',
        r'set reminder (.+?)(?:at |@)(\d{1,2}):?(\d{2})?\s*(am|pm)?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            task = match.group(1).strip()
            hour = int(match.group(2))
            minute = int(match.group(3)) if match.group(3) else 0
            period = match.group(4)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            
            reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reminder_time < datetime.now():
                reminder_time += timedelta(days=1)
            
            return {
                'task': task,
                'time': reminder_time,
                'created': datetime.now()
            }
    return None

# Display current chat name
st.caption(f"💬 {current_chat['name']}")

# File upload section
with st.expander("📎 Upload Files (Images, PDFs, Documents)", expanded=False):
    uploaded_file = st.file_uploader(
        "Upload an image, PDF, or document",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'txt', 'doc', 'docx'],
        key="file_uploader"
    )
    
    if uploaded_file:
        file_type = uploaded_file.type
        
        if file_type.startswith('image/'):
            image = Image.open(uploaded_file)
            st.image(image, caption=uploaded_file.name, use_container_width=True)
            if st.button("📤 Add to conversation"):
                st.session_state.uploaded_files.append({
                    'type': 'image',
                    'name': uploaded_file.name,
                    'data': image
                })
                st.success(f"✅ Added {uploaded_file.name}")
        
        elif file_type == 'application/pdf':
            st.info(f"📄 PDF: {uploaded_file.name}")
            if st.button("📤 Add to conversation"):
                st.session_state.uploaded_files.append({
                    'type': 'pdf',
                    'name': uploaded_file.name,
                    'data': uploaded_file.getvalue()
                })
                st.success(f"✅ Added {uploaded_file.name}")
        
        else:
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            st.text_area("File content preview:", content[:500], height=100)
            if st.button("📤 Add to conversation"):
                st.session_state.uploaded_files.append({
                    'type': 'text',
                    'name': uploaded_file.name,
                    'data': content
                })
                st.success(f"✅ Added {uploaded_file.name}")

# Show uploaded files
if st.session_state.uploaded_files:
    st.caption(f"📎 {len(st.session_state.uploaded_files)} file(s) attached")
    cols = st.columns(len(st.session_state.uploaded_files))
    for idx, file_info in enumerate(st.session_state.uploaded_files):
        with cols[idx]:
            st.caption(f"📄 {file_info['name']}")
            if st.button("❌", key=f"remove_file_{idx}"):
                st.session_state.uploaded_files.pop(idx)
                st.rerun()

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
    
    # Check for reminder
    reminder = extract_reminder(prompt)
    if reminder:
        st.session_state.reminders.append(reminder)
        reminder_msg = f"✅ Reminder set for {reminder['time'].strftime('%I:%M %p')}: {reminder['task']}"
        current_chat['messages'].append({"role": "assistant", "content": reminder_msg})
        with st.chat_message("assistant"):
            st.markdown(reminder_msg)
            st.balloons()
    else:
        # Auto-generate chat name from first message
        if len(current_chat['messages']) == 1:
            words = prompt.split()[:4]
            chat_name = ' '.join(words)
            if len(chat_name) > 30:
                chat_name = chat_name[:30] + "..."
            current_chat['name'] = chat_name.capitalize()
        
        # Get bot response with streaming
        with st.chat_message("assistant"):
            try:
                # Prepare message content
                message_parts = [prompt]
                
                # Add uploaded files to the message
                if st.session_state.uploaded_files:
                    for file_info in st.session_state.uploaded_files:
                        if file_info['type'] == 'image':
                            message_parts.append(file_info['data'])
                        elif file_info['type'] == 'text':
                            message_parts.append(f"\n\nFile: {file_info['name']}\n{file_info['data']}")
                    
                    # Clear uploaded files after sending
                    st.session_state.uploaded_files = []
                
                response = st.session_state.chat_instance.send_message(message_parts, stream=True)
                response_text = st.write_stream(response)
                current_chat['messages'].append({"role": "assistant", "content": response_text})
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                current_chat['messages'].append({"role": "assistant", "content": error_msg})

# Check for due reminders
current_time = datetime.now()
for reminder in st.session_state.reminders[:]:
    if reminder['time'] <= current_time:
        st.toast(f"🔔 Reminder: {reminder['task']}", icon="🔔")
        st.session_state.reminders.remove(reminder)

# Sidebar
with st.sidebar:
    st.header("Chat Sessions")
    
    if st.button("➕ New Chat", use_container_width=True):
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
    
    # Display reminders
    st.subheader("⏰ Active Reminders")
    if st.session_state.reminders:
        for idx, reminder in enumerate(st.session_state.reminders):
            time_left = reminder['time'] - datetime.now()
            hours = int(time_left.total_seconds() // 3600)
            minutes = int((time_left.total_seconds() % 3600) // 60)
            
            with st.container():
                st.markdown(f"""
                <div class="reminder-box">
                    <strong>{reminder['task']}</strong><br>
                    📅 {reminder['time'].strftime('%I:%M %p')}<br>
                    ⏱️ In {hours}h {minutes}m
                </div>
                """, unsafe_allow_html=True)
                if st.button("❌ Delete", key=f"del_reminder_{idx}"):
                    st.session_state.reminders.pop(idx)
                    st.rerun()
    else:
        st.caption("No active reminders")
    
    st.divider()
    
    # Display all chat sessions
    st.subheader("💬 Chats")
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

# Browser notification script (only refresh if there are reminders)
if st.session_state.reminders:
    st.markdown("""
    <script>
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Check reminders every 30 seconds
    setTimeout(function() {
        window.location.reload();
    }, 30000);
    </script>
    """, unsafe_allow_html=True)

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    **📎 Upload Files:**
    - Images (PNG, JPG, GIF, WebP)
    - PDFs and Documents
    - Text files
    - Ask questions about uploaded images
    
    **⏰ Set Reminders:**
    - "Remind me to call mom at 7:00 pm"
    - "Set reminder for meeting at 3:30 pm"
    - "Reminder to take medicine at 9:00 am"
    
    **💬 Chat Features:**
    - Multiple chat sessions
    - Streaming responses for faster replies
    - Auto-generated chat names
    
    **Note:** 
    - Allow notifications for reminders
    - Keep app open for reminders to work
    """)
