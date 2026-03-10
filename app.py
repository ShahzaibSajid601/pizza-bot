import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pizza Online AI", page_icon="🍕", layout="centered")

# --- CUSTOM CSS FOR "GOOD LOOKS" ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    .stChatInput { border-radius: 20px; }
    h1 { color: #FF4B4B; text-shadow: 2px 2px #000000; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍕 Pizza Online Assistant")
st.caption("Freshly baked AI logic for Zaib's Pizza Shop")

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
    # Make sure your CSV is in the same folder as app.py
    return pd.read_csv('pizza_sales.csv')

try:
    df = load_data()
except Exception as e:
    st.error(f"Data file not found: {e}")
    st.stop()

# --- AI SETUP ---
try:
    # Use st.secrets for deployment, fallback to string for local testing
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-lite')
except Exception as e:
    st.warning("AI Configuration Error. Bot will run in 'Offline Mode'.")
    model = None

# --- HYBRID BOT LOGIC ---
def get_response(user_input):
    user_input = user_input.lower().strip()
    
    # 1. ADDRESS CAPTURE
    if st.session_state.waiting_for_address:
        order_id = st.session_state.waiting_for_address
        st.session_state.active_orders[order_id]['address'] = user_input
        st.session_state.active_orders[order_id]['status'] = "Confirmed"
        st.session_state.waiting_for_address = None
        return f"✅ **Order Confirmed, Zaib!**\n\nYour order **{order_id}** will be delivered to: `{user_input}` via Cash on Delivery."

    # 2. LOCAL LOGIC: MENU
    if any(x in user_input for x in ["menu", "list"]):
        menu = df[['pizza_name', 'unit_price']].drop_duplicates('pizza_name').head(12)
        return "### 🍕 Our Professional Menu\n" + menu.to_string(index=False)

    # 3. LOCAL LOGIC: LOWEST PRICE (Fixes your specific query)
    if "lowest" in user_input or "cheapest" in user_input:
        cheapest = df.loc[df['unit_price'].idxmin()]
        return f"🤑 The most budget-friendly option is the **{cheapest['pizza_name']}** at only **${cheapest['unit_price']}**! Want to order it?"

    # 4. ORDERING SYSTEM
    matched_pizza = None
    for _, row in df.iterrows():
        if row['pizza_name'].lower() in user_input:
            matched_pizza = row
            break
            
    if matched_pizza is not None:
        oid = f"PZ-{random.randint(1000, 9999)}"
        st.session_state.active_orders[oid] = {
            "name": matched_pizza['pizza_name'],
            "price": matched_pizza['unit_price'],
            "status": "Awaiting Address"
        }
        st.session_state.waiting_for_address = oid
        return f"🛒 **{matched_pizza['pizza_name']}** added to cart!\n\n**Total: ${matched_pizza['unit_price']}**\n\nPlease enter your **Delivery Address** to finalize:"

    # 5. AI FALLBACK
    if model:
        try:
            prompt = f"Role: Pizza Shop Assistant. Context: {user_input}. Note: We only do Cash on Delivery."
            response = model.generate_content(prompt)
            return response.text
        except:
            return "I'm a bit overwhelmed! Try asking for the 'menu' or naming a pizza."
    return "Offline Mode: Please ask for the 'menu' or name a specific pizza."

# --- UI INTERFACE ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_response(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
