import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from pyrogram.errors import UserNotParticipant, FloodWait

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
JOIN_CHANNEL = "@h4ckerrmx" 
CHANNEL_LINK = "https://t.me/h4ckerrmx"

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_v21_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

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

# --- [ HELPERS ] ---
async def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    try:
        user = await app.get_chat_member(JOIN_CHANNEL, user_id)
        return user.status in ["member", "administrator", "creator"]
    except UserNotParticipant: return False
    except: return True # Error pe allow kar do taaki bot na phanse

def get_main_kb(user_id):
    kb = [
        ["📞 Number V1", "🚀 Number V3"],
        ["🔍 Truecaller Pro", "📧 Email Info"],
        ["🆔 TG ID", "🚗 Vehicle RC"],
        ["🌐 Web Scrape", "🎁 Refer & Earn"],
        ["👤 My Profile"]
    ]
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

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        if ref_id != 0 and ref_id != user_id:
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
            try: await client.send_message(ref_id, "🎁 **Referral Bonus!** You got `5` credits.")
            except: pass
        # New user gets 5 credits
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    if not await is_subscribed(user_id):
        return await message.reply_text("⚠️ **Join @h4ckerrmx first!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]]))
    
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_callback_query(filters.regex("verify_me"))
async def verify(client, callback_query):
    if await is_subscribed(callback_query.from_user.id):
        await callback_query.answer("✅ Verified!", show_alert=True)
        await callback_query.message.delete()
        await client.send_message(callback_query.from_user.id, "💎 **Welcome Back!**", reply_markup=get_main_kb(callback_query.from_user.id))
    else: await callback_query.answer("Join pehle kar bsdk! 😂🖕", show_alert=True)

@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    # --- [ ADMIN PANEL ] ---
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            return await message.reply_text(f"🛡 **ADMIN PANEL**\n\n👥 Total Users: `{total}`", reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🔙 Back"]], resize_keyboard=True))
        elif text == "📢 Broadcast":
            user_states[user_id] = "bc"
            return await message.reply_text("📝 Send Broadcast Message:", reply_markup=ForceReply(selective=True))
        elif text == "➕ Add Credits":
            user_states[user_id] = "add"
            return await message.reply_text("📝 Send: `USER_ID AMOUNT`", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 **Main Menu**", reply_markup=get_main_kb(user_id))

    # --- [ ADMIN ACTIONS ] ---
    if user_id in user_states:
        state = user_states[user_id]; del user_states[user_id]
        if state == "bc":
            cursor.execute("SELECT user_id FROM users")
            all_users = cursor.fetchall()
            for u in all_users:
                try: await client.send_message(u[0], f"📢 **ADMIN:**\n\n{text}"); await asyncio.sleep(0.05)
                except FloodWait as e: await asyncio.sleep(e.value)
                except: pass
            return await message.reply_text("✅ Broadcast Finished.")
        elif state == "add":
            try:
                tid, amt = text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid)))
                db.commit()
                return await message.reply_text(f"✅ Added {amt} to {tid}")
            except: return await message.reply_text("❌ Use Format: `ID AMOUNT`")

    # --- [ USER ACTIONS ] ---
    if not await is_subscribed(user_id): return

    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{u[0]}`\n🔎 Total: `{u[1]}`")

    if text == "🎁 Refer & Earn":
        bot = (await client.get_me()).username
        return await message.reply_text(f"🎁 **Refer & Earn**\nLink: `https://t.me/{bot}?start={user_id}`\n(5 Credits per Refer)")

    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    if user_id in user_states:
        service = user_states[user_id]; del user_states[user_id]
        if any(pid in text for pid in PROTECTED_IDS): return await message.reply_text("Baap ka data mat nikal! 😂🖕")
        
        await send_log(message.from_user, service, text)
        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            if r:
                await status.edit(f"✅ **Result:**\n\n```json\n{json.dumps(r, indent=4)}\n```")
                cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No records found.")
        except: await status.edit("❌ API Timeout/Error.")

app.run()
        
