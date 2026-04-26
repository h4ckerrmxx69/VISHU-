import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 # Tera ID

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"]

app = Client("soul_chaser_vfinal", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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
    "🚗 Vehicle Info": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO1?Rc_number={q}",
    "👤 Vehicle Owner": "https://intelx-premium-apipanel.vercel.app/INTELXDEMO2?Rc_number={q}",
    "🆔 Aadhaar Info": "http://intelx-premium-apipanel.vercel.app/INTELXDEMO4?AADHAR={q}"
}

user_states = {}

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [
        ["📞 Mobile Intelligence", "🆔 TG Num Lookup"],
        ["🚗 Vehicle Info", "👤 Vehicle Owner"],
        ["🆔 Aadhaar Info", "👤 My Profile"],
        ["🎁 Refer & Earn"]
    ]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ LOG & GHOST CLEANER ] ---
async def send_log(user, tool, query, alert=False):
    prefix = "⚠️ **SECURITY ALERT**" if alert else "📢 **New Request**"
    log_text = f"{prefix}\n👤 **User:** {user.first_name} ❤️\n🆔 **ID:** `{user.id}`\n🛠 **Tool:** {tool}\n📝 **Query:** `{query}`"
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

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
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        if ref_id and ref_id != user_id:
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
            try: await client.send_message(ref_id, "🎁 Referral Bonus! +5 Credits.")
            except: pass
        cursor.execute("INSERT INTO users (user_id, credits, referred_by) VALUES (?, 5, ?)", (user_id, ref_id))
        db.commit()
    user_states[user_id] = None
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text)
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # 1. PROFILE LOGIC (PRIORITY)
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        res = cursor.fetchone()
        creds = "♾ Unlimited" if user_id == ADMIN_ID else res[0]
        return await message.reply_text(f"👤 **PROFILE**\n\n💰 Credits: `{creds}`\n🔎 Searches: `{res[1]}`", reply_markup=get_main_kb(user_id))

    # 2. REFER & EARN LOGIC
    if text == "🎁 Refer & Earn":
        bot_usr = (await client.get_me()).username
        return await message.reply_text(f"🎁 **REFER & EARN**\n\nInvite link: `https://t.me/{bot_usr}?start={user_id}`", reply_markup=get_main_kb(user_id))

    # 3. ADMIN PANEL LOGIC
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 BOSS MODE", reply_markup=get_admin_kb())
        if text == "🔙 Back":
            user_states[user_id] = None
            return await message.reply_text("🔙 Returned to Menu", reply_markup=get_main_kb(user_id))
        if text in ["📢 Broadcast", "➕ Add Credits", "🚫 Ban User", "✅ Unban User"]:
            user_states[user_id] = f"ADMIN_{text}"
            return await message.reply_text(f"📝 Send input for {text}:")

    # 4. TOOL SELECTION
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ Credits khatam!", reply_markup=get_main_kb(user_id))
        user_states[user_id] = text
        return await message.reply_text(f"🚀 {text} Active! Direct number bhej:")

    # 5. STATE PROCESSING (INPUT HANDLING)
    state = user_states.get(user_id)
    if state:
        # Admin Action Handling
        if state.startswith("ADMIN_"):
            action = state.replace("ADMIN_", "")
            if action == "➕ Add Credits":
                try:
                    tid, amt = text.split()
                    cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                    user_states[user_id] = None
                    return await message.reply_text("✅ Credits Added!", reply_markup=get_admin_kb())
                except: return await message.reply_text("Format: `ID AMOUNT`")
            user_states[user_id] = None
            return

        # API Lookup Handling & Protection
        if state in API_MAP:
            if any(pid in text.replace(" ","") for pid in PROTECTED_IDS):
                await send_log(message.from_user, state, text, alert=True)
                return await message.reply_text("❌ Baap ka data mat nikal! 😂", reply_markup=get_main_kb(user_id))

            await send_log(message.from_user, state, text)
            status = await message.reply_text("🔎 Searching...")
            try:
                r = requests.get(API_MAP[state].format(q=text), timeout=25).json()
                clean = ghost_clean(r)
                await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2)}\n```", reply_markup=get_main_kb(user_id))
                if user_id != ADMIN_ID:
                    cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
                else:
                    cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
                user_states[user_id] = None
            except:
                await status.edit("❌ Error.", reply_markup=get_main_kb(user_id))

app.run()
