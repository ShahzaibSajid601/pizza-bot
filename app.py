import streamlit as st
import pandas as pd
import google.generativeai as genai
import random
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Pizza Online AI", page_icon="🍕", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    .stChatMessage { border-radius: 15px; border: 1px solid #30363d; margin-bottom: 10px; }
    h1 { color: #FF4B4B; text-shadow: 2px 2px #000000; font-family: 'Arial'; }
    .stChatInput { border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🍕 Pizza Online Assistant")
st.caption("Advanced Hybrid AI Logic | User: Zaib")

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

try:
    df = load_data()
    unique_menu = df[['pizza_name', 'unit_price']].drop_duplicates('pizza_name').sort_values('unit_price')
except Exception as e:
    st.error(f"CSV Load Error: {e}")
    st.stop()

# --- AI SETUP (Paste this in your Cell/App) ---
try:
    # 1. Get Key from Secrets
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    
    # 2. Use 'gemini-pro' - It is the most compatible version
    model = genai.GenerativeModel('gemini-pro') 
    
    # 3. Connection Test
    test_res = model.generate_content("Hi")
    st.sidebar.success("✅ Gemini AI is Now Online!")
except Exception as e:
    # Agar abhi bhi error aaye, toh exact detail sidebar mein dikhay ga
    st.sidebar.error(f"❌ Connection Error: {str(e)}")
    model = None
# --- HYBRID BOT LOGIC ---
def get_response(user_input):
    ui = user_input.lower().strip()
    
    # 1. GLOBAL CANCEL/REMOVE LOGIC
    if any(word in ui for word in ["cancel", "remove", "delete", "stop"]):
        if st.session_state.active_orders:
            last_id = list(st.session_state.active_orders.keys())[-1]
            removed_item = st.session_state.active_orders[last_id]['name']
            del st.session_state.active_orders[last_id]
            st.session_state.waiting_for_address = None
            return f"🗑️ Done Zaib! Aapka order ({removed_item}) cart se remove kar diya gaya hai."
        return "Aapka cart pehle hi khali hai!"

    # 2. ADDRESS CAPTURE
    if st.session_state.waiting_for_address:
        if len(ui) < 5:
            return "❌ Address bohat chota hai. Please provide a full delivery address:"
        
        oid = st.session_state.waiting_for_address
        st.session_state.active_orders[oid].update({"address": user_input, "status": "Confirmed"})
        st.session_state.waiting_for_address = None
        return f"✅ **Zabardast Zaib!** Order **{oid}** confirmed ho gaya hai. Hum jald hi aapke address `{user_input}` par pohnchain ge. (COD Only)"

    # 3. LOCAL LOGIC: MENU
    if any(x in ui for x in ["menu", "list", "items"]):
        items = unique_menu.head(12)
        return "### 🍕 Official Pizza Menu\n" + items.to_string(index=False)

    # 4. LOCAL LOGIC: PRICE / STATUS
    if any(x in ui for x in ["price", "total", "bill", "status", "track"]):
        if st.session_state.active_orders:
            res = "### 📋 Your Current Orders:\n"
            for oid, data in st.session_state.active_orders.items():
                res += f"- **{data['name']}**: ${data['price']} | Status: {data['status']}\n"
            return res
        return "Abhi tak koi order nahi mila. Menu dekhne ke liye 'menu' likhain."

    # 5. LOCAL LOGIC: LOWEST/FIRST
    if "lowest" in ui or "cheapest" in ui or "1st" in ui:
        cheapest = unique_menu.iloc[0]
        return f"🤑 Humara sab se sasta pizza **{cheapest['pizza_name']}** hai, sirf **${cheapest['unit_price']}** mein. Kya main ye order kar doon?"

    # 6. ORDERING SYSTEM (CSV MATCHING)
    matched_pizza = None
    for _, row in unique_menu.iterrows():
        if row['pizza_name'].lower() in ui:
            matched_pizza = row
            break
            
    if matched_pizza is not None:
        oid = f"PZ-{random.randint(1000, 9999)}"
        st.session_state.active_orders[oid] = {
            "name": matched_pizza['pizza_name'],
            "price": matched_pizza['unit_price'],
            "status": "Waiting for Address"
        }
        st.session_state.waiting_for_address = oid
        return f"🛒 **{matched_pizza['pizza_name']}** cart mein add ho gaya! (Total: ${matched_pizza['unit_price']})\n\nAb apna **Delivery Address** bataein:"

 # --- PART 7: SMART AI FALLBACK (Updated) ---
def get_ai_fallback(user_input):
    if model:
        try:
            # Building a clean prompt without complex chat history objects
            order_summary = "None"
            if st.session_state.active_orders:
                order_summary = str(st.session_state.active_orders)

            prompt = f"""
            You are 'Pizza Online Assistant' for Zaib's shop.
            Current Orders: {order_summary}
            User Question: {user_input}
            Rules: Only talk about pizza and the shop. Be very short (1-2 lines).
            """
            
            # Simple direct generation is more stable than chat.send_message
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"AI is thinking... (Details: {str(e)[:50]})"
    return "Offline Mode: Type 'menu' or a pizza name to continue."

# --- UI INTERFACE ---
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


