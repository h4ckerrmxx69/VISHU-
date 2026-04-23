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

# 🛡️ PROTECTION LIST
PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_v10_fixed", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB & GHOST CLEANER ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT, referred_by INTEGER)")
db.commit()

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

NUM_BACKUPS = [
    "https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}",
    "https://yash-code-ai-free-api.alphamovies.workers.dev/?number={q}",
    "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}"
]
TG_ID_BACKUP = "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}"

user_states = {}

async def is_subscribed(user_id):
    if user_id == ADMIN_ID: return True
    try:
        member = await app.get_chat_member(JOIN_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except: return False

def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG Username", "🆔 TG ID"], ["🆔 Aadhaar Info", "👨‍👩‍👧 Family Info"], ["🌐 Web Scrape", "🚗 Vehicle RC"], ["🎁 Refer & Earn", "👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active', ?)", (user_id, ref_id))
        db.commit()
    if not await is_subscribed(user_id):
        return await message.reply_text(f"⚠️ Join {JOIN_CHANNEL} to use bot.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)], [InlineKeyboardButton("Verify ✅", callback_data="verify_me")]]))
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text & ~filters.command(["start", "addcredits"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            cursor.execute("SELECT COUNT(*) FROM users")
            u_count = cursor.fetchone()[0]
            return await message.reply_text(f"🛡 **ADMIN PANEL**\n\n👥 Users: `{u_count}`\n🔒 Protection: `ACTIVE ({len(PROTECTED_IDS)})`", reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits Info"], ["🔙 Back"]], resize_keyboard=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 **Main Menu**", reply_markup=get_main_kb(user_id))

    if user_id in user_states:
        service = user_states[user_id]
        if any(pid in text for pid in PROTECTED_IDS):
            await client.send_message(ADMIN_ID, f"🚫 **Abuse Alert!** `{user_id}` targetted `{text}`")
            del user_states[user_id]
            return await message.reply_text("Madarchod, baap ka data nikalega? Nikal yahan se bsdk! 😂🖕")

        status = await message.reply_text("🔎 Searching...")
        final_data = None

        try:
            # Main API Call
            resp = requests.get(API_MAP[service].format(q=text), timeout=10).json()
            
            # Agar Main API fail ho (Empty data, Error, ya Limit)
            if not resp or "data" not in str(resp) or "limit" in str(resp).lower() or "error" in str(resp).lower():
                # 🔄 AUTOMATIC BACKUP SWITCH
                if "Number" in service:
                    for b_url in NUM_BACKUPS:
                        try:
                            backup_resp = requests.get(b_url.format(q=text), timeout=10).json()
                            if backup_resp and "data" in str(backup_resp):
                                resp = backup_resp
                                break
                        except: continue
                elif service == "🆔 TG ID":
                    try:
                        backup_resp = requests.get(TG_ID_BACKUP.format(q=text)).json()
                        if backup_resp: resp = backup_resp
                    except: pass
            
            final_data = ghost_clean(resp)
            if final_data:
                await status.edit(f"**✅ Result:**\n\n```json\n{json.dumps(final_data, indent=4)}\n```")
                if user_id != ADMIN_ID: cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
                else: cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No data found in Main or Backup APIs.")
        except Exception as e:
            await status.edit(f"❌ API Crash: {str(e)}")
        del user_states[user_id]
        return

    if text == "👤 My Profile":
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        c = "Unlimited" if user_id == ADMIN_ID else u[1]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{c}`\n🔎 Total: `{u[2]}`")

    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if user_id != ADMIN_ID and cursor.fetchone()[0] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Enter Query for {text}:")

app.run()
        
