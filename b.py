# ----------------------
# Imports
# ----------------------
import streamlit as st
import openai
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import threading

# ----------------------
# OpenAI API Key
# ----------------------
openai.api_key = "YOUR_OPENAI_API_KEY"

# ----------------------
# Streamlit Session Memory
# ----------------------
if "history" not in st.session_state:
    st.session_state.history = []

SAFE_FALLBACK = (
    "I cannot diagnose, but I can give guidance. "
    "For mild symptoms, rest, hydrate, and monitor your condition. "
    "If symptoms worsen, please consult a healthcare professional."
)

# ----------------------
# AI Chat Function
# ----------------------
def chat_ai(message):
    st.session_state.history.append({"role": "user", "content": message})
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": (
                    "You are a helpful AI health assistant. "
                    "Provide guidance based on user symptoms. "
                    "Highlight emergencies. Use simple language."
                )}
            ] + st.session_state.history,
            temperature=0.7,
            max_tokens=400
        )
        reply = response['choices'][0]['message']['content'].strip()
    except Exception:
        reply = SAFE_FALLBACK

    st.session_state.history.append({"role": "assistant", "content": reply})
    return reply

# ----------------------
# Streamlit UI
# ----------------------
st.title("💬 AI Health Chatbot")

# User input in Streamlit
user_input = st.text_input("You:", key="input")

if st.button("Send") and user_input:
    bot_reply = chat_ai(user_input)
    st.text_area("Chatbot:", value=bot_reply, height=200, key="bot_output")

# Display chat history
st.markdown("### Chat History")
for chat in st.session_state.history:
    role = "You" if chat["role"] == "user" else "Chatbot"
    st.markdown(f"**{role}:** {chat['content']}")

# ----------------------
# Flask App for Twilio SMS
# ----------------------
app = Flask(__name__)

@app.route("/sms", methods=['POST'])
def sms_reply():
    incoming_msg = request.form.get('Body')
    
    # Call the same AI function
    reply_text = chat_ai(incoming_msg)
    
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

# Run Flask server in separate thread to not block Streamlit
def run_flask():
    app.run(port=5000)

threading.Thread(target=run_flask, daemon=True).start()
