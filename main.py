import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_fixed", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER DEFAULT 5, 
    searches INTEGER DEFAULT 0, 
    status TEXT DEFAULT 'active', 
    referred_by INTEGER DEFAULT 0)""")
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

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["cyber_xsupport", "cyber", "xsupport", "intelx", "apipanel", "premium", "owner", "developer", "http", "t.me", "@", "sakib", "rohit", "ayaanmods", "powered"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    elif isinstance(data, str):
        if any(w in data.lower() for w in banned): return None
    return data

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

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT INTO users (user_id, credits) VALUES (?, 5)", (user_id,))
        db.commit()
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text & ~filters.command("start"))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # 1. Profile Logic (Top Priority)
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n\n💰 Credits: `{u[0]}`\n🔎 Searches: `{u[1]}`", reply_markup=get_main_kb(user_id))

    # 2. Admin Logic
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 **BOSS MODE**", reply_markup=get_admin_kb())
        elif text in ["📢 Broadcast", "➕ Add Credits", "🚫 Ban User", "✅ Unban User"]:
            user_states[user_id] = text
            return await message.reply_text(f"📝 Proceed with {text}:", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 Main Menu", reply_markup=get_main_kb(user_id))

    # Admin State Processing
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states.pop(user_id)
        if state == "➕ Add Credits":
            try:
                tid, amt = text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                return await message.reply_text(f"✅ Added {amt} to {tid}", reply_markup=get_admin_kb())
            except: return await message.reply_text("❌ Error! ID AMOUNT bhej.", reply_markup=get_admin_kb())
        # ... baaki admin states ...

    # 3. Refer & Earn
    if text == "🎁 Refer & Earn":
        bot = (await client.get_me()).username
        return await message.reply_text(f"🎁 Invite & Earn Credits!\n🔗 `https://t.me/{bot}?start={user_id}`", reply_markup=get_main_kb(user_id))

    # 4. Search Tools Initiation
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ Credits khatam!", reply_markup=get_main_kb(user_id))
        return await message.reply_text(f"📝 Send input for {text}:", reply_markup=ForceReply(selective=True))

    # 5. API Execution (Handling the Reply)
    if message.reply_to_message and "Send input for" in message.reply_to_message.text:
        service = message.reply_to_message.text.split("for ")[-1].strip(":")
        
        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=20).json()
            clean = ghost_clean(r)
            # Yahan humne reply_markup=get_main_kb(user_id) add kiya hai
            await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2, ensure_ascii=False)}\n```", reply_markup=get_main_kb(user_id))
            cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
            db.commit()
        except:
            await status.edit("❌ Error or Timeout.", reply_markup=get_main_kb(user_id))

app.run()
