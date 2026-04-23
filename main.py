import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 

# ID Protection (Inka data koi nahi nikal payega)
PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DATABASE SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER DEFAULT 5, 
    searches INTEGER DEFAULT 0, 
    status TEXT DEFAULT 'active', 
    referred_by INTEGER)""")
db.commit()

# --- [ API MAPPING ] ---
API_MAP = {
    "📞 Number V1": "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}",
    "🚀 Number V3": "https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}",
    "🔍 Truecaller Pro": "https://rohittruecallerapi.vercel.app/info?number={q}",
    "📧 Email Info": "https://rohitemailapi.vercel.app/info?mail={q}",
    "🆔 TG ID": "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}",
    "🚗 Vehicle RC": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
    "🌐 Web Scrape": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
}

user_states = {}

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["owner", "developer", "api_dev", "api_updates", "credit", "dm", "buy", "access", "@", "http", "t.me", "sakib", "rohit", "froxtdevil", "ayaanmods"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in k.lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data if not (isinstance(data, str) and any(w in data.lower() for w in banned)) else None

# --- [ LOG SYSTEM ] ---
async def send_log(user, tool, query):
    log_text = (
        f"📢 **New Request Log**\n"
        f"👤 **Name:** {user.first_name} ❤️\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"🔗 **Username:** @{user.username if user.username else 'None'}\n"
        f"🛠 **Tool:** {tool}\n"
        f"📝 **Query:** `{query}`"
    )
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

# --- [ ADMIN HELPERS ] ---
def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ START & MENU ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == "banned":
        return await message.reply_text("❌ **Banned!** Baap se panga mat le. 😂🖕")

    if not res:
        cursor.execute("INSERT INTO users (user_id, status) VALUES (?, 'active')", (user_id,))
        db.commit()

    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# --- [ ADMIN PANEL LOGIC ] ---
@app.on_message(filters.text & ~filters.command("start"))
async def main_handler(client, message):
    user_id = message.from_user.id
    text = message.text

    # Check Ban
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    if res and res[0] == "banned": return

    # Admin Panel Navigation
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 **ADMIN CONTROLS**", reply_markup=get_admin_kb())
        elif text == "📢 Broadcast":
            user_states[user_id] = "bc"
            return await message.reply_text("📝 Send Message for Broadcast:", reply_markup=ForceReply(selective=True))
        elif text == "➕ Add Credits":
            user_states[user_id] = "add"
            return await message.reply_text("📝 Format: `ID AMOUNT`", reply_markup=ForceReply(selective=True))
        elif text == "🚫 Ban User":
            user_states[user_id] = "ban"
            return await message.reply_text("📝 Send User ID to Ban:", reply_markup=ForceReply(selective=True))
        elif text == "✅ Unban User":
            user_states[user_id] = "unban"
            return await message.reply_text("📝 Send User ID to Unban:", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "👤 My Profile"], ["📊 Admin Panel"]]
            return await message.reply_text("💎 **Main Menu**", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

    # Handle Admin States (Broadcast, Ban, Credits)
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states.pop(user_id)
        if state == "bc":
            cursor.execute("SELECT user_id FROM users"); all_u = cursor.fetchall()
            for u in all_u:
                try: await client.send_message(u[0], f"📢 **ADMIN:**\n\n{text}"); await asyncio.sleep(0.1)
                except: pass
            return await message.reply_text("✅ Broadcast Done.")
        elif state == "add":
            try:
                tid, amt = text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                return await message.reply_text(f"✅ Added {amt} to {tid}")
            except: return await message.reply_text("❌ Error.")
        elif state == "ban":
            cursor.execute("UPDATE users SET status = 'banned' WHERE user_id=?", (int(text),)); db.commit()
            return await message.reply_text("🚫 User Banned.")
        elif state == "unban":
            cursor.execute("UPDATE users SET status = 'active' WHERE user_id=?", (int(text),)); db.commit()
            return await message.reply_text("✅ User Unbanned.")

    # Search Tools Processing
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ No Credits!")
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    # API Execution Logic
    if message.reply_to_message and "Send Query for" in message.reply_to_message.text:
        service = message.reply_to_message.text.split("for ")[-1].strip(":")
        
        if any(pid in text for pid in PROTECTED_IDS):
            return await message.reply_text("Baap ka data mat nikal bsdk! 😂🖕")

        await send_log(message.from_user, service, text)
        status = await message.reply_text("🔎 **Searching...**")
        
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            clean = ghost_clean(r)
            if clean:
                await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=2)}\n```")
                cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No clean records found.")
        except: await status.edit("❌ API Timeout/Error.")

app.run()
