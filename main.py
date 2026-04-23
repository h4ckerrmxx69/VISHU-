import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
JOIN_CHANNEL = "@h4ckerrmx" 
CHANNEL_LINK = "https://t.me/h4ckerrmx"

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_v17_referral", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DATABASE SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
# 'referred_by' column added for referral tracking
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
        member = await app.get_chat_member(JOIN_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "🎁 Refer & Earn"], ["👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def send_log(user, tool, query):
    log_text = (
        f"📢 **New Request Log**\n👤 **Name:** {user.first_name} ❤️\n🆔 **User ID:** `{user.id}`\n🔗 **Username:** @{user.username if user.username else 'None'}\n🛠 **Tool:** {tool}\n📝 **Query:** `{query}`"
    )
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

# --- [ START & REFERRAL LOGIC ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_exists = cursor.fetchone()

    if not user_exists:
        # Check if joined via referral link (e.g., /start 12345)
        ref_id = 0
        if len(message.command) > 1:
            try:
                ref_id = int(message.command[1])
                if ref_id != user_id:
                    # Give 5 credits to the Referrer
                    cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
                    try: await client.send_message(ref_id, "🎁 **Referral Bonus!** You got `5` credits for inviting a friend.")
                    except: pass
            except: ref_id = 0
        
        # New user gets 5 credits
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    if not await is_subscribed(user_id):
        return await message.reply_text("⚠️ **Join @h4ckerrmx first!**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]]))
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

# --- [ TEXT HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start", "addcredits"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 **ADMIN PANEL**", reply_markup=ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 **Main Menu**", reply_markup=get_main_kb(user_id))

    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        c = "Unlimited" if user_id == ADMIN_ID else u[0]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{c}`\n🔎 Total Searches: `{u[1]}`")

    if text == "🎁 Refer & Earn":
        bot_username = (await client.get_me()).username
        refer_link = f"https://t.me/{bot_username}?start={user_id}"
        return await message.reply_text(f"🎁 **Refer & Earn**\n\nInvite your friends and get **5 Credits** per refer!\n\nYour Link:\n`{refer_link}`")

    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        creds = cursor.fetchone()[0]
        if user_id != ADMIN_ID and creds < 1:
            return await message.reply_text("❌ **No Credits!** Refer friends or contact Admin.")
        
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    if user_id in user_states:
        service = user_states[user_id]
        del user_states[user_id]

        if any(pid in text for pid in PROTECTED_IDS):
            await send_log(message.from_user, f"🛡️ ABUSE ALERT: {service}", text)
            return await message.reply_text("Madarchod, baap ka data nikalega? 😂🖕")

        await send_log(message.from_user, service, text)
        status = await message.reply_text("🔎 Searching...")
        
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            clean = ghost_clean(r)
            if clean:
                await status.edit(f"**✅ Result:**\n\n```json\n{json.dumps(clean, indent=4)}\n```")
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                if user_id != ADMIN_ID:
                    cursor.execute("UPDATE users SET credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No data found.")
        except: await status.edit("❌ API Error.")

@app.on_callback_query(filters.regex("verify_me"))
async def verify_cb(client, callback_query):
    if await is_subscribed(callback_query.from_user.id):
        await callback_query.message.delete()
        await client.send_message(callback_query.from_user.id, "💎 **Verified!**", reply_markup=get_main_kb(callback_query.from_user.id))
    else: await callback_query.answer("Join pehle kar bsdk! 😂", show_alert=True)

app.run()
    
