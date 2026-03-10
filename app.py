import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pizza Online AI", page_icon="🍕")
st.title("🍕 Pizza Online AI Assistant")

# --- INITIALIZE SESSION STATE (Memory) ---
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

# --- AI SETUP ---
# On Deployment, we hide the API Key in "Secrets"
genai.configure(api_key=st.secrets["AIzaSyB3k0JR3CRrlQH7P8ed3CXbBSFfKi4CE5I"])
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# --- BOT LOGIC ---
def get_response(user_input):
    user_input = user_input.lower().strip()
    
    # 1. Address Logic
    if st.session_state.waiting_for_address:
        order_id = st.session_state.waiting_for_address
        st.session_state.active_orders[order_id]['address'] = user_input
        st.session_state.active_orders[order_id]['status'] = "Confirmed"
        st.session_state.waiting_for_address = None
        return f"✅ Thanks Zaib! Order {order_id} is confirmed for delivery to: {user_input}"

    # 2. Menu Logic
    if "menu" in user_input:
        menu = df[['pizza_name', 'unit_price']].drop_duplicates('pizza_name').head(10)
        return "--- 🍕 MENU ---\n" + menu.to_string(index=False)

    # 3. Search CSV for Pizza
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
        return f"✅ {matched_pizza['pizza_name']} selected (${matched_pizza['unit_price']}). Please enter your ADDRESS:"

    # 4. AI Fallback
    response = model.generate_content(f"You are a pizza bot. User said: {user_input}")
    return response.text

# --- DISPLAY CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me for the menu or order a pizza..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = get_response(prompt)
    
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})