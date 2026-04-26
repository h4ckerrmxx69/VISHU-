import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 # Tera ID

# In IDs ka data koi nahi nikal payega (Admin ID aur tere extra IDs)
PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_protected", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
    "🚗 Vehicle Info": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO1?Rc_number={q}",
    "👤 Vehicle Owner": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO2?Rc_number={q}",
    "🆔 Aadhaar Info": "http://intelx-premium-apipanel.vercel.app/INTELXDEMO4?AADHAR={q}"
}

user_states = {}

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [["📞 Mobile Intelligence", "🆔 TG Num Lookup"], ["🚗 Vehicle Info", "👤 Vehicle Owner"], ["🆔 Aadhaar Info", "👤 My Profile"], ["🎁 Refer & Earn"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- [ LOG SYSTEM ] ---
async def send_log(user, tool, query, alert=False):
    prefix = "⚠️ **SECURITY ALERT**" if alert else "📢 **New Request**"
    log_text = (
        f"{prefix}\n"
        f"👤 **User:** {user.first_name} ❤️\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🛠 **Tool:** {tool}\n"
        f"📝 **Query:** `{query}`"
    )
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["cyber_xsupport", "intelx", "apipanel", "premium", "owner", "developer", "http", "t.me", "@", "powered"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data

# --- [ COMMANDS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()
    user_states[user_id] = None
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

# --- [ MAIN LOGIC ] ---
@app.on_message(filters.text)
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # Basic Buttons
    if text == "👤 My Profile":
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        creds = "♾ Unlimited" if user_id == ADMIN_ID else cursor.fetchone()[0]
        return await message.reply_text(f"💰 Credits: `{creds}`", reply_markup=get_main_kb(user_id))

    if text in API_MAP:
        user_states[user_id] = text
        return await message.reply_text(f"🚀 **{text}** Active! Input bhejo:")

    # State Processing & PROTECTION
    state = user_states.get(user_id)
    if state and state in API_MAP:
        
        # 🛡️ HARD PROTECTION LOGIC 🛡️
        # Agar query mein Protected IDs ka koi bhi hissa hai, toh block karo
        query_clean = text.replace(" ", "").strip()
        if any(pid in query_clean for pid in PROTECTED_IDS):
            await send_log(message.from_user, state, text, alert=True)
            user_states[user_id] = None
            return await message.reply_text("❌ **Access Denied!** Baap ka data nikalne ki koshish mat kar bsdk. 😂🖕", reply_markup=get_main_kb(user_id))

        # Regular Search
        await send_log(message.from_user, state, text)
        status = await message.reply_text("🔎 Fetching...")
        
        try:
            r = requests.get(API_MAP[state].format(q=text), timeout=25).json()
            clean = ghost_clean(r)
            await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2)}\n```", reply_markup=get_main_kb(user_id))
            
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            user_states[user_id] = None
        except:
            await status.edit("❌ API Error.", reply_markup=get_main_kb(user_id))

app.run()
    
