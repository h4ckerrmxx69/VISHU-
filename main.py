import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply
from pyrogram.errors import UserNotParticipant

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
JOIN_CHANNEL = "h4ckerrmx" 
CHANNEL_LINK = "https://t.me/h4ckerrmx"

# Jis ID ka data hide rakhna hai yahan add kar do
PROTECTED_IDS = [str(ADMIN_ID), "5192884021"] 

app = Client("soul_chaser_protected", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT, referred_by INTEGER)")
db.commit()

# --- [ GHOST CLEANER ] ---
def ghost_clean(data):
    banned = ["owner", "owners", "developer", "developers", "api_dev", "api_updates", "credit", "credits", "dm", "buy", "access", "@", "http", "t.me", "sakib", "rohit", "froxtdevil", "kon_hu_mai"]
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k.lower() in banned: continue
            if isinstance(v, str) and any(word in v.lower() for word in banned): continue
            cleaned_v = ghost_clean(v)
            if cleaned_v is not None: new_dict[k] = cleaned_v
        return new_dict if new_dict else None
    return data

# --- [ APIs & BACKUPS ] ---
API_MAP = {
    "📞 Number V1": "https://sbsakib.eu.cc/apis/num_v1?key=Demo&num={q}",
    "🚀 Number V3": "https://sbsakib.eu.cc/apis/num_v3?key=Demo&Info={q}",
    "🔍 Truecaller Pro": "https://rohittruecallerapi.vercel.app/info?number={q}",
    "📧 Email Info": "https://rohitemailapi.vercel.app/info?mail={q}",
    "🆔 TG Username": "https://sbsakib.eu.cc/apis/tg_username?key=Demo&username={q}",
    "🆔 TG ID": "https://sbsakib.eu.cc/apis/tg_id?key=Demo&term={q}",
    "🆔 Aadhaar Info": "https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id={q}",
    "👨‍👩‍👧 Family Info": "https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term={q}",
    "🚗 Vehicle RC": "https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc={q}",
    "🌐 Web Scrape": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
    "🎮 Free Fire": "https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid={q}",
}

NUM_BACKUPS = ["https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}", "https://yash-code-ai-free-api.alphamovies.workers.dev/?number={q}"]
TG_ID_BACKUP = "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}"

user_states = {}

# --- [ HELPERS ] ---
async def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    try:
        await app.get_chat_member(JOIN_CHANNEL, user_id)
        return True
    except UserNotParticipant: return False
    except: return True

def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG Username", "🆔 TG ID"], ["🆔 Aadhaar Info", "👨‍👩‍👧 Family Info"], ["🌐 Web Scrape", "🚗 Vehicle RC"], ["🎁 Refer & Earn", "👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- [ CALLBACK FOR VERIFY ] ---
@app.on_callback_query(filters.regex("verify_me"))
async def verify_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if await is_subscribed(user_id):
        cursor.execute("SELECT referred_by FROM users WHERE user_id=?", (user_id,))
        ref_data = cursor.fetchone()
        if ref_data and ref_data[0] != 0:
            referrer_id = ref_data[0]
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (referrer_id,))
            cursor.execute("UPDATE users SET referred_by = 0 WHERE user_id=?", (user_id,))
            db.commit()
            try: await client.send_message(referrer_id, f"🎁 **Referral Bonus!**\nAapko **5 Credits** mil gaye!")
            except: pass
        await callback_query.answer("Verified! ✅", show_alert=True)
        await callback_query.message.delete()
        await client.send_message(user_id, "💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))
    else:
        await callback_query.answer("Join pehle kar bsdk! ❌", show_alert=True)

# --- [ START ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    ref_id = 0
    if len(message.command) > 1:
        try:
            ref_id = int(message.command[1])
            if ref_id == user_id: ref_id = 0
        except: pass

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()

    if not await is_subscribed(user_id):
        return await message.reply_text(f"⚠️ Join @h4ckerrmx to use this bot.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]]))
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    if not await is_subscribed(user_id):
        return await message.reply_text("⚠️ Verify Karo!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]]))

    # Admin Panel
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            cursor.execute("SELECT COUNT(*) FROM users")
            return await message.reply_text(f"🛡 **ADMIN PANEL**\n\nTotal: `{cursor.fetchone()[0]}`", reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "🔙 Back"]], resize_keyboard=True))
        elif text == "📢 Broadcast":
            user_states[user_id] = "WAIT_BC"
            return await message.reply_text("📣 Send message:", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            return await start(client, message)

    if user_id == ADMIN_ID and user_states.get(user_id) == "WAIT_BC":
        cursor.execute("SELECT user_id FROM users")
        for u in cursor.fetchall():
            try: await client.send_message(u[0], text)
            except: continue
        del user_states[user_id]
        return await message.reply_text("✅ Sent!")

    # Search Logic
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or user[3] == 'banned': return

    if text == "👤 My Profile":
        c = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{c}`\n🔎 Total: `{user[2]}`")

    if text == "🎁 Refer & Earn":
        bot_user = (await client.get_me()).username
        return await message.reply_text(f"🎁 **Refer & Earn**\n\nLink: `https://t.me/{bot_user}?start={user_id}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Enter query for {text}:")

    if user_id in user_states:
        service = user_states[user_id]
        
        # --- [ PROTECTION LOGIC ] ---
        # Agar query mein koi protected ID hai
        if any(pid in text for pid in PROTECTED_IDS):
            log_msg = (f"🚫 **Abuse Attempt Log**\n👤 Name: {message.from_user.first_name}\n🆔 User ID: `{user_id}`\n🛠 Tool: {service}\n📝 Target: `{text}`")
            await client.send_message(ADMIN_ID, log_msg)
            del user_states[user_id]
            return await message.reply_text("Madarchod, baap ka data nikalega? Nikal yahan se bsdk! 😂🖕")

        status = await message.reply_text("🔎 Searching...")
        log_msg = (f"📢 **New Request Log**\n👤 Name: {message.from_user.first_name}\n🆔 User ID: `{user_id}`\n🛠 Tool: {service}\n📝 Query: `{text}`")
        await client.send_message(ADMIN_ID, log_msg)

        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            # Backups
            if "Number" in service and ("limit" in str(r).lower() or not r.get("data")):
                for b_url in NUM_BACKUPS:
                    try:
                        r = requests.get(b_url.format(q=text)).json()
                        if r and "data" in str(r): break
                    except: continue
            
            clean_res = ghost_clean(r)
            if clean_res:
                await status.edit(f"**✅ Result:**\n\n```json\n{json.dumps(clean_res, indent=4)}\n```")
                if user_id != ADMIN_ID: cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
                else: cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No data found.")
        except: await status.edit("❌ API Error.")
        del user_states[user_id]

app.run()
        
