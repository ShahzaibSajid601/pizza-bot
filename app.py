import streamlit as st
import pandas as pd
import requests
import json
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pizza Online AI", page_icon="🍕")
st.title("🍕 Pizza Online Assistant")

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
    
    # UPDATE: Using 'gemini-1.0-pro' because 1.5-flash is not being found in your project
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.0-pro:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        # Safety settings are kept empty to avoid any rejection
        "safetySettings": [] 
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        # Checking for successful response
        if 'candidates' in result:
            return result['candidates'][0]['content']['parts'][0]['text']
        elif 'error' in result:
            # Displaying the exact model list if it fails again
            return f"Model Error: {result['error']['message']}. Please check AI Studio."
        else:
            return "AI is sleeping. But the Pizza Oven is ON! Use 'menu' to order."
            
    except Exception as e:
        return "Connection Error. Please try again later."
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



