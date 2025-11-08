import google.generativeai as genai
import os

# Configure the Gemini API
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set")
    print("Please set it with: set GEMINI_API_KEY=your_api_key_here")
    exit(1)

genai.configure(api_key=API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-2.5-flash')

# Start chat session
chat = model.start_chat(history=[])

print("Gemini Chatbot - Type 'quit' or 'exit' to end the conversation\n")

while True:
    user_input = input("You: ").strip()
    
    if user_input.lower() in ['quit', 'exit']:
        print("Goodbye!")
        break
    
    if not user_input:
        continue
    
    try:
        response = chat.send_message(user_input)
        print(f"\nBot: {response.text}\n")
    except Exception as e:
        print(f"Error: {e}\n")
