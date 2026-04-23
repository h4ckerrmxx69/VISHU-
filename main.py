import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
JOIN_CHANNEL = "@h4ckerrmx" #
CHANNEL_LINK = "https://t.me/h4ckerrmx"

# 🛡️ PROTECTION LIST (Yahan aur IDs add kar sakte ho)
PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_final_v14", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DATABASE SETUP ] ---
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

# --- [ NEW API MAPPING (NO SAKIB) ] ---
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
    kb = [
        ["📞 Number V1", "🚀 Number V3"],
        ["🔍 Truecaller Pro", "📧 Email Info"],
        ["🆔 TG ID", "🚗 Vehicle RC"],
        ["🌐 Web Scrape", "🎁 Refer & Earn"],
        ["👤 My Profile"]
    ]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- [ START COMMAND ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    if not await is_subscribed(user_id):
        return await message.reply_text(
            "⚠️ **Access Denied!**\n\nYou must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]
            ])
        )
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

# --- [ VERIFY BUTTON FIXED ] ---
@app.on_callback_query(filters.regex("verify_me"))
async def verify_handler(client, callback_query):
    user_id = callback_query.from_user.id
    if await is_subscribed(user_id):
        await callback_query.answer("Verified! Welcome back. 🚀", show_alert=True)
        await callback_query.message.delete()
        await client.send_message(user_id, "💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))
    else:
        await callback_query.answer("Abe join toh kar pehle bsdk! 😂🖕", show_alert=True)

# --- [ MAIN TEXT HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start", "addcredits"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    if not await is_subscribed(user_id): return

    # Admin Logic
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            cursor.execute("SELECT COUNT(*) FROM users")
            return await message.reply_text(f"🛡 **ADMIN PANEL**\n\nTotal: `{cursor.fetchone()[0]}`", 
                reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits Info"], ["🔙 Back"]], resize_keyboard=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 **Main Menu**", reply_markup=get_main_kb(user_id))

    # Profile & Refer
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{'Unlimited' if user_id == ADMIN_ID else u[0]}`\n🔎 Total: `{u[1]}`")

    # Service Selection
    if text in API_MAP:
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    # Search Logic
    if user_id in user_states:
        service = user_states[user_id]
        del user_states[user_id] # State clear to prevent loops

        if any(pid in text for pid in PROTECTED_IDS):
            return await message.reply_text("Madarchod, baap ka data nikalega? 😂🖕")

        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            clean = ghost_clean(r)
            if clean:
                await status.edit(f"**✅ Result:**\n\n```json\n{json.dumps(clean, indent=4)}\n```")
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                if user_id != ADMIN_ID: cursor.execute("UPDATE users SET credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No data found.")
        except: await status.edit("❌ API Error. Try later.")

app.run()
                
