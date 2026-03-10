import streamlit as st
import pandas as pd
import requests
import json
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pizza Online AI", page_icon="🍕")
st.title("Pizza Online Assistant")

# --- INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_orders" not in st.session_state:
    st.session_state.active_orders = {}
if "waiting_for_address" not in st.session_state:
    st.session_state.waiting_for_address = None

# --- LOAD DATA ---
@st.cache_data
def load_data():
    return pd.read_csv('pizza_sales.csv')

df = load_data()

# --- DIRECT API CALL FUNCTION (No library needed) ---
def call_gemini_api(prompt):
    api_key = st.secrets["GEMINI_API_KEY"]
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    # --- STEP 1: GET AVAILABLE MODELS ---
    list_url = f"{base_url}/models?key={api_key}"
    try:
        models_resp = requests.get(list_url).json()
        # Hum dhoondenge ke list mein kaunsa model 'generateContent' support karta hai
        available_models = [m['name'] for m in models_resp.get('models', []) 
                            if 'generateContent' in m.get('supportedGenerationMethods', [])]
        
        if not available_models:
            return "AI Error: No compatible models found in your project."
        
        # Sab se behtar model select karna (Prefer Flash or Pro)
        selected_model = available_models[0] 
        for m in available_models:
            if "flash" in m:
                selected_model = m
                break
    except Exception as e:
        return f"Discovery Error: {str(e)}"

    # --- STEP 2: CALL THE SELECTED MODEL ---
    gen_url = f"{base_url}/{selected_model}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(gen_url, headers=headers, json=payload)
        result = response.json()
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        return f"Error: {result.get('error', {}).get('message', 'Unknown response format')}"
    except:
        return "AI is taking a break. Use 'menu' to order manually!"
# --- BOT LOGIC ---
def get_response(user_input):
    ui = user_input.lower().strip()
    
    # 1. Address Logic
    if st.session_state.waiting_for_address:
        order_id = st.session_state.waiting_for_address
        st.session_state.active_orders[order_id]['address'] = user_input
        st.session_state.active_orders[order_id]['status'] = "Confirmed"
        st.session_state.waiting_for_address = None
        return f"✅ **Confirmed!** Order {order_id} is set for: `{user_input}`"

    # 2. Menu Logic
    if "menu" in ui:
        menu = df[['pizza_name', 'unit_price']].drop_duplicates('pizza_name').head(10)
        return "### 🍕 Pizza Menu\n" + menu.to_string(index=False)

    # 3. Ordering System
    matched_pizza = None
    for _, row in df.iterrows():
        if row['pizza_name'].lower() in ui:
            matched_pizza = row
            break
            
    if matched_pizza is not None:
        oid = f"PZ-{random.randint(1000, 9999)}"
        st.session_state.active_orders[oid] = {"name": matched_pizza['pizza_name'], "price": matched_pizza['unit_price']}
        st.session_state.waiting_for_address = oid
        return f"🛒 **{matched_pizza['pizza_name']}** added ($ {matched_pizza['unit_price']}). Please enter your **Address**:"

    # 4. AI Fallback (Direct Request)
    return call_gemini_api(f"You are a Pizza Shop Bot. User says: {user_input}")

# --- UI DISPLAY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask for menu or order a pizza..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_response(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})






