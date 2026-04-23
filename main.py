import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from pyrogram.errors import UserNotParticipant, FloodWait

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 # Tera Fix ID

# ✨ ID PROTECTION LIST ✨
PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

JOIN_CHANNEL = -1001807190033 # Numeric ID hi use karna
CHANNEL_LINK = "https://t.me/h4ckerrmx"

app = Client("soul_chaser_ultimate", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER, 
    searches INTEGER, 
    status TEXT, 
    referred_by INTEGER)""")
db.commit()

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["owner", "developer", "api_dev", "api_updates", "credit", "dm", "buy", "access", "@", "http", "t.me", "sakib", "rohit", "froxtdevil", "ayaanmods"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in k.lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    return data if not (isinstance(data, str) and any(w in data.lower() for w in banned)) else None

# --- [ HELPERS ] ---
async def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    try:
        user = await app.get_chat_member(JOIN_CHANNEL, user_id)
        return user.status in ["member", "administrator", "creator"]
    except: return False

def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "🎁 Refer & Earn"], ["👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

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

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        if ref_id != 0 and ref_id != user_id:
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
            try: await client.send_message(ref_id, "🎁 **Referral Bonus!** 5 Credits added.")
            except: pass
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    if await is_subscribed(user_id):
        await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))
    else:
        await message.reply_text(
            "⚠️ **Access Restricted!**\n\nJoin our channel to continue. The bot will auto-verify once you join.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]
            ])
        )

@app.on_callback_query(filters.regex("verify_me"))
async def verify(client, callback_query):
    if await is_subscribed(callback_query.from_user.id):
        await callback_query.answer("✅ Auto-Verified!", show_alert=True)
        await callback_query.message.delete()
        await client.send_message(callback_query.from_user.id, "💎 **Menu Unlocked!**", reply_markup=get_main_kb(callback_query.from_user.id))
    else:
        await callback_query.answer("Join pehle kar bsdk! 😂🖕", show_alert=True)

@app.on_message(filters.text & ~filters.command("start"))
async def handle_text(client, message):
    user_id = message.from_user.id
    if not await is_subscribed(user_id): return

    # --- Admin Panel ---
    if user_id == ADMIN_ID:
        if message.text == "📊 Admin Panel":
            cursor.execute("SELECT COUNT(*) FROM users"); total = cursor.fetchone()[0]
            return await message.reply_text(f"🛡 **ADMIN PANEL**\n\n👥 Users: `{total}`", reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🔙 Back"]], resize_keyboard=True))
        elif message.text == "📢 Broadcast":
            user_states[user_id] = "bc"; return await message.reply_text("📝 Send Message:", reply_markup=ForceReply(selective=True))
        elif message.text == "➕ Add Credits":
            user_states[user_id] = "add"; return await message.reply_text("📝 `ID AMOUNT`", reply_markup=ForceReply(selective=True))
        elif message.text == "🔙 Back":
            return await message.reply_text("💎 **Main Menu**", reply_markup=get_main_kb(user_id))

    # --- Admin Actions ---
    if user_id in user_states:
        state = user_states.pop(user_id)
        if state == "bc":
            cursor.execute("SELECT user_id FROM users"); users = cursor.fetchall()
            for u in users:
                try: await client.send_message(u[0], f"📢 **ADMIN:**\n\n{message.text}"); await asyncio.sleep(0.05)
                except: pass
            return await message.reply_text("✅ Done.")
        elif state == "add":
            try:
                tid, amt = message.text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                return await message.reply_text(f"✅ Added {amt} to {tid}")
            except: return await message.reply_text("❌ Format Error.")

    # --- User Features ---
    if message.text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{u[0]}`\n🔎 Total: `{u[1]}`")

    if message.text == "🎁 Refer & Earn":
        bot = (await client.get_me()).username
        return await message.reply_text(f"🎁 **Refer & Earn**\n`https://t.me/{bot}?start={user_id}`")

    if message.text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = message.text
        return await message.reply_text(f"📝 Send Query for {message.text}:", reply_markup=ForceReply(selective=True))

    # --- Search Logic with Protection & Logs ---
    if user_id in user_states:
        service = user_states.pop(user_id)
        
        # 🛡️ ID PROTECTION 🛡️
        if any(pid in message.text for pid in PROTECTED_IDS):
            return await message.reply_text("Baap ka data mat nikal bsdk! 😂🖕")
        
        # ✨ SEND LOG ✨
        await send_log(message.from_user, service, message.text)
        
        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=message.text), timeout=15).json()
            # ✨ GHOST CLEAN ✨
            clean = ghost_clean(r)
            if clean:
                await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(clean, indent=4)}\n```")
                cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No clean data found.")
        except: await status.edit("❌ API Error/Timeout.")

app.run()
    
