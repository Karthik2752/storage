import streamlit as st
import requests

# Hugging Face API Configuration
API_URL = "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-1.3B"
API_TOKEN = "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"  # Replace with your Hugging Face API token

headers = {
    "Authorization": f"Bearer {API_TOKEN}"
}

# App Title
st.title("🌾 Crop Predictor")
st.subheader("Maximize Profit with Comprehensive Crop Planning")

# Sidebar Input
st.sidebar.header("Input Features")
soil_ph = st.sidebar.slider("Soil pH", 0.0, 14.0, 6.5)
soil_type = st.sidebar.selectbox("Soil Type", ["Sandy", "Loamy", "Clay", "Silt"])
water_availability = st.sidebar.slider("Water Availability (liters/month)", 1000, 100000, step=1000)
climate = st.sidebar.selectbox("Climate", ["Tropical", "Dry", "Temperate", "Continental", "Polar"])
budget = st.sidebar.number_input("Budget (in ₹)", min_value=10000, step=1000)
home_state = st.sidebar.selectbox("Your State in India", [
    "Andhra Pradesh", "Maharashtra", "Punjab", "Bihar", "Uttar Pradesh", 
    "West Bengal", "Tamil Nadu", "Gujarat", "Kerala", "Rajasthan", "Karnataka", 
    "Haryana", "Madhya Pradesh", "Assam", "Odisha", "Telangana", "Other"
])
month = st.sidebar.selectbox("Month of Cultivation", [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
])

# User Input Summary
input_data = {
    "Soil pH": soil_ph,
    "Soil Type": soil_type,
    "Water Availability (liters/month)": water_availability,
    "Climate": climate,
    "Budget (₹)": budget,
    "Home State": home_state,
    "Planning Month": month
}

st.write("### Your Inputs:")
st.json(input_data)

# Function to Get Crop Recommendation from Hugging Face API
def get_crop_recommendation(input_data):
    prompt = (
        f"Suggest a profitable crop for the following conditions:\n"
        f"Soil pH: {input_data['Soil pH']}\n"
        f"Soil Type: {input_data['Soil Type']}\n"
        f"Water Availability: {input_data['Water Availability (liters/month)']} liters\n"
        f"Climate: {input_data['Climate']}\n"
        f"Budget: ₹{input_data['Budget (₹)']}\n"
        f"Home State: {input_data['Home State']}\n"
        f"Planning Month: {input_data['Planning Month']}\n"
        f"Output should include:\n"
        f"1. Recommended crop.\n"
        f"2. Target state(s) for demand in India.\n"
        f"3. Expected profit and investment breakdown.\n"
        f"4. End products from the crop and profit potential.\n"
        f"5. Chemicals and resources required (seeds, labor, tools).\n"
        f"6. Risks during the crop period.\n"
        f"7. Other suggestions for better returns."
    )
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return f"Error: {response.status_code}, {response.json()}"

# Generate Crop Recommendations
st.write("## Crop Recommendation:")
try:
    crop_recommendations = get_crop_recommendation(input_data)
    st.success("### Detailed Recommendations and Insights:")
    st.write(crop_recommendations)
except Exception as e:
    st.error(f"Error generating crop recommendations: {e}")

# About Section
st.write("## About This App")
st.info("This app uses AI to recommend profitable crops tailored to your inputs, "
        "including detailed investment breakdowns, risks, end products, and demand across India.")
