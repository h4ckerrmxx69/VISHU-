import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 # Tera Fix ID

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_intelx_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# --- [ NEW INTELX API MAPPING ] ---
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
    banned = ["intelx", "apipanel", "premium", "owner", "developer", "http", "t.me", "@", "sakib", "rohit", "ayaanmods"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data

# --- [ LOG SYSTEM ] ---
async def send_log(user, tool, query):
    log_text = (f"📢 **NEW REQUEST**\n👤 {user.first_name}\n🆔 `{user.id}`\n🛠 {tool}\n📝 `{query}`")
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [["📞 Mobile Intelligence", "🆔 TG Num Lookup"], ["🚗 Vehicle Info", "👤 Vehicle Owner"], ["📑 Aadhaar Lookup", "👨‍👩‍👦 Family Data"], ["🎁 Refer & Earn", "👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ START & REFERRAL ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == "banned":
        return await message.reply_text("❌ Tu Banned hai bsdk! 😂🖕")

    if not res:
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        if ref_id != 0 and ref_id != user_id:
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
            try: await client.send_message(ref_id, "🎁 Referral Bonus: +5 Credits!")
            except: pass
        cursor.execute("INSERT INTO users (user_id, credits, status, referred_by) VALUES (?, 5, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

# --- [ MAIN HANDLER (ADMIN + TOOLS) ] ---
@app.on_message(filters.text & ~filters.command("start"))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # Admin Navigation
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 **BOSS MODE ACTIVE**", reply_markup=get_admin_kb())
        elif text in ["📢 Broadcast", "➕ Add Credits", "🚫 Ban User", "✅ Unban User"]:
            user_states[user_id] = text
            return await message.reply_text(f"📝 Proceed with {text}:", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 Main Menu", reply_markup=get_main_kb(user_id))

    # Admin Action
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states.pop(user_id)
        if state == "📢 Broadcast":
            cursor.execute("SELECT user_id FROM users"); users = cursor.fetchall()
            for u in users:
                try: await client.send_message(u[0], f"📢 **ADMIN:**\n\n{text}"); await asyncio.sleep(0.05)
                except: pass
            return await message.reply_text("✅ Done.", reply_markup=get_admin_kb())
        elif state == "➕ Add Credits":
            try:
                tid, amt = text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                return await message.reply_text(f"✅ Added {amt} to {tid}", reply_markup=get_admin_kb())
            except: return await message.reply_text("❌ ID AMOUNT bhej.")

    # Profile & Refer
    if text == "👤 My Profile":
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        return await message.reply_text(f"💰 Credits: `{cursor.fetchone()[0]}`")

    # Search Execution
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ No Credits!")
        return await message.reply_text(f"📝 Send input for {text}:", reply_markup=ForceReply(selective=True))

    if message.reply_to_message and "Send input for" in message.reply_to_message.text:
        service = message.reply_to_message.text.split("for ")[-1].strip(":")
        if any(pid in text for pid in PROTECTED_IDS): return await message.reply_text("Baap ka data nahi! 😂🖕")
        
        await send_log(message.from_user, service, text)
        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=20).json()
            clean = ghost_clean(r)
            await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2)}\n```")
            cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
            db.commit()
        except: await status.edit("❌ API Error.")

app.run()
              
