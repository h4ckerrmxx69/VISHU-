import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_final_fix", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
    # placeholder set kiya taaki keyboard hamesha visible rahe
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, placeholder="Select a Tool...")

def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["cyber_xsupport", "intelx", "apipanel", "premium", "owner", "developer", "http", "t.me", "@", "sakib", "rohit", "powered"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    # DB check and Welcome
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text & ~filters.command("start"))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # Admin Panel Check
    if user_id == ADMIN_ID and text == "📊 Admin Panel":
        return await message.reply_text("🛡 BOSS MODE", reply_markup=get_admin_kb())

    # Profile Check
    if text == "👤 My Profile":
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        res = cursor.fetchone()
        return await message.reply_text(f"💰 Credits: `{res[0]}`", reply_markup=get_main_kb(user_id))

    # Tool Selection
    if text in API_MAP:
        return await message.reply_text(f"📝 Send input for {text}:", reply_markup=ForceReply(selective=True))

    # API Request Processing
    if message.reply_to_message and "Send input for" in message.reply_to_message.text:
        service = message.reply_to_message.text.split("for ")[-1].strip(":")
        
        # Security Check
        if any(pid in text for pid in PROTECTED_IDS):
            return await message.reply_text("Baap ka data mat nikal! 😂", reply_markup=get_main_kb(user_id))

        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=20).json()
            clean = ghost_clean(r)
            
            # CRITICAL FIX: Result ke saath main keyboard wapas bhej rahe hain
            await status.edit(
                f"✅ **Result Found:**\n\n```json\n{json.dumps(clean, indent=2, ensure_ascii=False)}\n```", 
                reply_markup=get_main_kb(user_id)
            )
            # Credit update logic...
        except:
            await status.edit("❌ API Error.", reply_markup=get_main_kb(user_id))

app.run()
