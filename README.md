# Gemini Chatbot

A simple chatbot using Google's Gemini API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. Set your API key as an environment variable:
```bash
set GEMINI_API_KEY=your_api_key_here
```

## Usage

### Web UI (Streamlit - Recommended)
Run the chatbot with a black theme UI:
```bash
streamlit run app.py
```

### Command Line
Run the basic chatbot:
```bash
python chatbot.py
```

Type your messages and press Enter. Type 'quit' or 'exit' to end the conversation.
