import streamlit as st
import openai
import re
import textwrap
from difflib import get_close_matches

# ----------------------
# OpenAI API key
# ----------------------
openai.api_key = "YOUR_OPENAI_API_KEY"  # replace with your OpenAI API key

# ----------------------
# Knowledge base
# ----------------------
KB = {
    'fever': 'For fever: rest, stay hydrated, and take **PARACETAMOL (Crocin, Calpol)** if needed. If temperature >39°C or persists >2-3 days, see a doctor.',
    'headache': 'For headache: rest, hydrate, avoid bright lights, and take **PARACETAMOL (Crocin, Calpol)** or **IBUPROFEN (Brufen, Combiflam)** if needed. Seek medical help if severe or sudden.',
    'dengue': '⚠️ Dengue may cause high fever, body pain, and rash. There is no specific medicine; consult a healthcare provider for testing and supportive care.',
    'malaria': '⚠️ Malaria can cause fever, chills, and headache. Get tested and seek antimalarial treatment if necessary.',
    'cough': 'For cough: stay hydrated, use a humidifier, and rest. For mild cough, **DEXTROMETHORPHAN syrup (Benadryl, Corex)** may help. See a doctor if persistent.',
    'cold': 'For common cold: rest, drink warm fluids, and take **ANTIHISTAMINES (Cetirizine, Allegra)** or **DECONGESTANTS (Vicks, Otrivin)** if needed. Consult a doctor if symptoms worsen.',
    'sore throat': 'For sore throat: gargle warm salt water, take **LOZENGES (Strepsils, Vicks)**, stay hydrated, and rest. Seek medical help if severe or persistent.',
    'vomiting': 'For vomiting: stay hydrated with **ORS**. Over-the-counter anti-nausea medicines like **Domstal** may help. See a doctor if persistent.',
    'diarrhea': 'For diarrhea: stay hydrated using **ORS (Electral, Hydralyte)**, avoid fatty foods, and use **Loperamide (Imodium)** for mild cases. Consult a doctor if severe.',
    'fatigue': 'For fatigue: rest, maintain a balanced diet, and ensure proper sleep. **Multivitamins (Revital, Nutrilite)** may help. See a doctor if prolonged.',
    'chills': 'For chills: keep warm, rest, and monitor temperature. **PARACETAMOL (Crocin, Calpol)** can help if fever is present.',
    'rash': 'For rash: avoid scratching, keep the area clean, and use **ANTIHISTAMINE CREAMS (Candid, Betnovate)**. See a dermatologist if severe.',
    'allergy': 'For mild allergy: take **ANTIHISTAMINES (Cetirizine, Allegra)** and avoid triggers. Seek medical attention if difficulty breathing or swelling occurs.',
    'eye irritation': 'For eye irritation: rinse with clean water, avoid rubbing, and use **LUBRICATING DROPS (Refresh, Tears Naturale)**. Consult a doctor if it worsens.',
    'stomach pain': 'For stomach pain: rest, avoid spicy foods, and take **ANTACIDS (Gelusil, Digene)**. See a doctor if pain is severe.',
    'chest pain': '⚠️ First Aid: Sit down, stay calm, chew **ASPIRIN (Disprin, Ecosprin)** if available, and call emergency immediately. Could indicate a heart attack.'
}

SAFE_FALLBACK = (
    "I cannot diagnose, but I can give guidance. For mild symptoms, rest, hydrate, and monitor your condition. "
    "If symptoms worsen, please consult a healthcare professional."
)

# ----------------------
# Symptom combination rules
# ----------------------
SYMPTOM_RULES = {
    frozenset(['fever', 'rash']): "⚠️ Fever with rash could indicate **dengue**. Consult a doctor immediately.",
    frozenset(['fever', 'headache', 'chills']): "⚠️ Fever + headache + chills could indicate **malaria**. Get tested promptly.",
    frozenset(['stomach pain', 'vomiting']): "⚠️ Stomach pain + vomiting may indicate **gastrointestinal infection**. Stay hydrated, see a doctor.",
    frozenset(['cough', 'fever', 'sore throat']): "⚠️ Cough + fever + sore throat may indicate **flu/respiratory infection**.",
    frozenset(['diarrhea', 'vomiting', 'fever']): "⚠️ Diarrhea + vomiting + fever may indicate **severe stomach infection**. Seek help immediately.",
    frozenset(['cough', 'shortness of breath', 'chest pain']): "🚨 Emergency: Could be **pneumonia/asthma/heart issue**. Seek hospital immediately!"
}

# ----------------------
# Session store
# ----------------------
if "sessions" not in st.session_state:
    st.session_state.sessions = {}

# ----------------------
# Helper functions
# ----------------------
def extract_keywords(text):
    text = text.lower().split()
    keywords_found = []
    for symptom in KB.keys():
        if get_close_matches(symptom, text, cutoff=0.6):
            keywords_found.append(symptom)
    return keywords_found

def check_symptom_combinations(symptoms):
    alerts = []
    user_symptoms_set = set(symptoms)
    for rule_symptoms, alert_message in SYMPTOM_RULES.items():
        if rule_symptoms.issubset(user_symptoms_set):
            alerts.append(alert_message)
    return alerts

def format_for_display(text, width=80):
    import textwrap
    wrapped_lines = textwrap.wrap(text, width=width)
    return "\n".join(wrapped_lines)

# ----------------------
# Chatbot logic
# ----------------------
def chat(user_id, message):
    if user_id not in st.session_state.sessions:
        st.session_state.sessions[user_id] = {'symptoms': []}

    keywords = extract_keywords(message)

    if keywords:
        st.session_state.sessions[user_id]['symptoms'].extend(k for k in keywords if k not in st.session_state.sessions[user_id]['symptoms'])
        responses = [KB[k] for k in keywords]
        reply = ' '.join(responses)
    else:
        reply = SAFE_FALLBACK

    if st.session_state.sessions[user_id]['symptoms']:
        reply += "\n\n📝 Your reported symptoms so far: " + ", ".join(st.session_state.sessions[user_id]['symptoms'])

    alerts = check_symptom_combinations(st.session_state.sessions[user_id]['symptoms'])
    if alerts:
        reply += "\n\n🚨 Alerts:\n" + "\n".join(alerts)

    return reply

# ----------------------
# Streamlit UI
# ----------------------
st.title("💬 AI Health Chatbot")

user_id = "user1"
user_input = st.text_input("You:", key="input")

if st.button("Send") and user_input:
    bot_reply = chat(user_id, user_input)
    st.text_area("Chatbot:", value=format_for_display(bot_reply), height=200, key="bot_output")

# Display chat history
st.markdown("### Chat History")
if user_id in st.session_state.sessions:
    for symptom in st.session_state.sessions[user_id]['symptoms']:
        st.markdown(f"- {symptom}")
