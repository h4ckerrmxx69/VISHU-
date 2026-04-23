import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DATABASE SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
# Table mein referred_by aur searches dono fix hain
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER DEFAULT 5, 
    searches INTEGER DEFAULT 0, 
    status TEXT DEFAULT 'active', 
    referred_by INTEGER DEFAULT 0)""")
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

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "🎁 Refer & Earn"], ["👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- [ START & REFERRAL LOGIC ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == "banned":
        return await message.reply_text("❌ **Banned!** Baap se panga mat le. 😂🖕")

    # Naya User Logic
    if not res:
        ref_id = 0
        # Check if joined via referral link
        if len(message.command) > 1:
            try:
                ref_id = int(message.command[1])
                if ref_id != user_id:
                    # Give 5 credits to the referrer
                    cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
                    try: 
                        await client.send_message(ref_id, f"🎁 **Referral Bonus!**\nNaya user `{user_id}` join hua, aapko **5 Credits** mil gaye.")
                    except: pass
            except: pass
        
        # New user gets 5 credits by default
        cursor.execute("INSERT INTO users (user_id, credits, searches, status, referred_by) VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
        welcome_msg = "🎁 **Welcome!** Naya account banane par aapko **5 Credits** mile hain."
    else:
        welcome_msg = "💎 **SOUL CHASER SUPREME** 💎"

    await message.reply_text(welcome_msg, reply_markup=get_main_kb(user_id))

# --- [ HANDLERS ] ---
@app.on_message(filters.text & ~filters.command("start"))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    # Admin Panel & User Profile Logic
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n\n💰 Credits: `{u[0]}`\n🔎 Searches: `{u[1]}`")

    if text == "🎁 Refer & Earn":
        bot = (await client.get_me()).username
        return await message.reply_text(f"🎁 **Refer & Earn**\n\nInvite your friends and get **5 Credits** per referral!\n\n🔗 `https://t.me/{bot}?start={user_id}`")

    # API Request Initiation
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        creds = cursor.fetchone()[0]
        if creds < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ **No Credits!** Refer karke earn karo.")
        
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    # API Execution
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
                await status.edit(f"✅ **Result Found:**\n\n```json\n{json.dumps(clean, indent=2)}\n```")
                # Deduct Credit and Update Search Count
                cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else:
                await status.edit("❌ No record found.")
        except:
            await status.edit("❌ API Error.")

app.run()
