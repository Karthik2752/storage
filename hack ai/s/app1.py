import streamlit as st
from huggingface_hub import InferenceClient


# Hugging Face API Key
HF_API_KEY = "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"

# App Title
st.title("🌾 Crop Predictor")
st.subheader("Maximize Profit with Comprehensive Crop Planning")

# About Section
st.write("## About This App")
st.info("This app uses an open-source Hugging Face model to recommend profitable crops tailored to your inputs, "
        "including detailed investment breakdowns, risks, end products, and demand across India.")

# Sidebar Input
st.sidebar.header("Input Features")
soil_ph = st.sidebar.slider("Soil pH", 0.0, 14.0, 6.5)
rainfall = st.sidebar.slider("Rainfall (cm/year)", 0, 500, 100)
soil_type = st.sidebar.selectbox("Soil Type", ["Sandy", "Loamy", "Clay", "Silt"])
climate = st.sidebar.selectbox("Climate", ["Tropical", "Dry", "Temperate", "Continental", "Polar"])
acres = st.sidebar.number_input("Available Land (in Acres)", min_value=1)
investment = st.sidebar.number_input("Investment Plan (₹)", min_value=5000, step=1000)
state = st.sidebar.selectbox("Your State", [
    "Andhra Pradesh", "Maharashtra", "Punjab", "Bihar", "Uttar Pradesh",
    "West Bengal", "Tamil Nadu", "Gujarat", "Kerala", "Rajasthan", "Karnataka",
    "Haryana", "Madhya Pradesh", "Assam", "Odisha", "Telangana", "Other"
])
district = st.sidebar.text_input("District")
borewells = st.sidebar.number_input("Number of Borewells", min_value=0)
water_sources = st.sidebar.text_area("Other Water Sources (if any)")
crop_type = st.sidebar.selectbox("Preferred Crop Type", ["Vegetables", "Grains", "Fruits", "Industrial"])
rotation_suggestion = st.sidebar.selectbox("Need Crop Rotation Suggestions?", ["Yes", "No"])

# User Input Summary
input_data = {
    "Soil pH": soil_ph,
    "Rainfall (cm/year)": rainfall,
    "Soil Type": soil_type,
    "Climate": climate,
    "Available Land (Acres)": acres,
    "Investment Plan (₹)": investment,
    "State": state,
    "District": district,
    "Borewells": borewells,
    "Other Water Sources": water_sources,
    "Preferred Crop Type": crop_type,
    "Crop Rotation Suggestion": rotation_suggestion
}

st.write("### Your Inputs:")
st.json(input_data)

# Hugging Face Model Setup
@st.cache_resource
def get_hf_client():
    return InferenceClient(api_key=HF_API_KEY)

# Generate Recommendations
st.write("## Crop Recommendation:")
try:
    client = get_hf_client()
    prompt = (f"Suggest a crop plan based on these inputs:\n"
              f"Soil pH: {soil_ph}\n"
              f"Rainfall: {rainfall} cm/year\n"
              f"Soil Type: {soil_type}\n"
              f"Climate: {climate}\n"
              f"Available Land: {acres} acres\n"
              f"Investment Plan: ₹{investment}\n"
              f"State: {state}\n"
              f"District: {district}\n"
              f"Borewells: {borewells}\n"
              f"Other Water Sources: {water_sources}\n"
              f"Preferred Crop Type: {crop_type}\n"
              f"Crop Rotation Suggestion: {rotation_suggestion}\n"
              f"Output should include:\n"
              f"1. Suitable crop options based on the inputs.\n"
              f"2. Detailed crop requirements: water, soil, seeds, etc.\n"
              f"3. Potential diseases and their prevention.\n"
              f"4. Total cost estimation and breakdown.\n"
              f"5. End-product opportunities and waste management.\n"
              f"6. Government-funded schemes supporting the crop.\n"
              f"7. Additional suggestions for profitability (e.g., companion crops).")
    
    response_parts = []
    for message in client.chat_completion(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        stream=True,
    ):
        response_parts.append(message.choices[0].delta.content)
    # Combine all parts into a single response
    full_response = ''.join(response_parts)

    # Render Output in Styled Sections
    st.write("### Recommendations")
    recommendations = full_response.split("\n\n")  # Split the response into sections
    for idx, section in enumerate(recommendations):
        st.markdown(f"#### Section {idx + 1}")
        st.write(section)
except Exception as e:
    st.error(f"Error generating crop recommendations: {e}")
