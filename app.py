import re
import textwrap
from deep_translator import GoogleTranslator
from difflib import get_close_matches

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
sessions = {}

# ----------------------
# Helpers
# ----------------------
def extract_keywords(text):
    text = text.lower().split()
    keywords_found = []
    for symptom in KB.keys():
        # Fuzzy matching: detect symptom even if typed roughly
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

# ----------------------
# Translation with deep-translator
# ----------------------
def translate_message(text, lang="en"):
    if lang == "en":
        return text
    try:
        clean_text = text.replace("\n", " ")
        translated = GoogleTranslator(source='en', target=lang).translate(clean_text)
        translated = translated.replace("🚨 Alerts:", "\n\n🚨 Alerts:")
        return translated
    except Exception:
        return text + " (⚠️ Translation unavailable)"

# ----------------------
# Format text for console display
# ----------------------
def format_for_console(text, width=80):
    wrapped_lines = textwrap.wrap(text, width=width)
    return "\n".join(wrapped_lines)

def chat(user_id, message, lang="en"):
    if user_id not in sessions:
        sessions[user_id] = {'symptoms': []}

    keywords = extract_keywords(message)

    if keywords:
        sessions[user_id]['symptoms'].extend(k for k in keywords if k not in sessions[user_id]['symptoms'])
        responses = [KB[k] for k in keywords]
        reply = ' '.join(responses)
    else:
        reply = SAFE_FALLBACK

    if sessions[user_id]['symptoms']:
        reply += "\n\n📝 Your reported symptoms so far: " + ", ".join(sessions[user_id]['symptoms'])

    alerts = check_symptom_combinations(sessions[user_id]['symptoms'])
    if alerts:
        reply += "\n\n🚨 Alerts:\n" + "\n".join(alerts)

    translated = translate_message(reply, lang)
    return translated

# ----------------------
# Interactive chatbot
# ----------------------
print("💬 AI Health Chatbot is online! (type 'exit' to quit)")
print("👉 You can also type 'lang hi' for Hindi or 'lang te' for Telugu")

user_id = "user1"
current_lang = "en"

while True:
    user_msg = input("You: ")
    if user_msg.lower() == "exit":
        print("Chatbot: Goodbye! Stay healthy 👋")
        break
    elif user_msg.lower().startswith("lang "):
        new_lang = user_msg.split(" ")[1]
        current_lang = new_lang
        print(f"🌐 Language switched to: {current_lang}")
        continue

    bot_reply = chat(user_id, user_msg, lang=current_lang)
    print("Chatbot:")
    print(format_for_console(bot_reply))
    print()
