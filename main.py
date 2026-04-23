import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"]

app = Client("soul_chaser_final_v3", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER DEFAULT 5, 
    searches INTEGER DEFAULT 0, 
    status TEXT DEFAULT 'active')""")
db.commit()

# --- [ API MAPPING ] ---
API_MAP = {
    "📞 Mobile Intelligence": "http://intelx-premium-apipanel.vercel.app/INTELXDEMO3?NUMBER={q}",
    "🆔 TG Num Lookup": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO?USERID={q}",
    "🚗 Vehicle Info": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO?USERID={q}",
    "👤 Vehicle Owner": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO2?Rc_number={q}",
    "📑 Aadhaar Lookup": "http://intelx-premium-apipanel.vercel.app/INTELXDEMO4?AADHAR={q}",
    "👨‍👩‍👦 Family Data": "http://intelx-premium-apipanel.vercel.app/INTELXDEMO5?FADHAR={q}"
}

# User state storage
user_states = {}

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [
        ["📞 Mobile Intelligence", "🆔 TG Num Lookup"],
        ["🚗 Vehicle Info", "👤 Vehicle Owner"],
        ["📑 Aadhaar Lookup", "👨‍👩‍👦 Family Data"],
        ["🎁 Refer & Earn", "👤 My Profile"]
    ]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["cyber_xsupport", "intelx", "apipanel", "premium", "owner", "developer", "http", "t.me", "@", "powered"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()
    user_states[user_id] = None
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text)
async def handle_logic(client, message):
    user_id = message.from_user.id
    text = message.text

    # 1. Profile & Back Logic
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        res = cursor.fetchone()
        creds = "Unlimited" if user_id == ADMIN_ID else res[0]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{creds}`\n🔎 Searches: `{res[1]}`", reply_markup=get_main_kb(user_id))
    
    if text == "🔙 Back":
        user_states[user_id] = None
        return await message.reply_text("💎 Main Menu", reply_markup=get_main_kb(user_id))

    # 2. Admin Panel Buttons
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 BOSS MODE", reply_markup=get_admin_kb())
        if text in ["📢 Broadcast", "➕ Add Credits", "🚫 Ban User", "✅ Unban User"]:
            user_states[user_id] = f"ADMIN_{text}"
            return await message.reply_text(f"📝 Send input for {text}:")

    # 3. Tool Selection
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        creds = cursor.fetchone()[0]
        if creds < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ No Credits!", reply_markup=get_main_kb(user_id))
        
        user_states[user_id] = text # State set kar di
        return await message.reply_text(f"🚀 {text} Active! Ab direct number/ID bhej do:")

    # 4. Processing States (No Reply Needed)
    state = user_states.get(user_id)
    if state:
        # Admin Action Processing
        if state.startswith("ADMIN_"):
            action = state.replace("ADMIN_", "")
            if action == "➕ Add Credits":
                try:
                    tid, amt = text.split()
                    cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                    user_states[user_id] = None
                    return await message.reply_text(f"✅ Added {amt} credits to {tid}", reply_markup=get_admin_kb())
                except: return await message.reply_text("❌ Format: `ID AMOUNT`")
            # Yahan baaki Admin actions (Ban/Broadcast) handle honge...
            user_states[user_id] = None
            return

        # API Search Processing
        if state in API_MAP:
            if any(pid in text for pid in PROTECTED_IDS):
                return await message.reply_text("Baap ka data nahi! 😂🖕", reply_markup=get_main_kb(user_id))

            status = await message.reply_text("🔎 Searching...")
            try:
                r = requests.get(API_MAP[state].format(q=text), timeout=20).json()
                clean = ghost_clean(r)
                await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2, ensure_ascii=False)}\n```", reply_markup=get_main_kb(user_id))
                
                if user_id != ADMIN_ID:
                    cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                else:
                    cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
                user_states[user_id] = None # Search khatam, state clear
            except:
                await status.edit("❌ API Error.", reply_markup=get_main_kb(user_id))

app.run()
                       
