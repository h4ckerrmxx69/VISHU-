import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
LOG_CHANNEL = ADMIN_ID 

app = Client("soul_chaser_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ NO BRANDING CLEANER ] ---
def clean_response(data):
    banned = ["owner", "owners", "developer", "developers", "channel", "credits", "link", "by", "website", "api_by", "success", "status", "msg", "credit"]
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k.lower() not in banned}
    elif isinstance(data, list):
        return [clean_response(i) for i in data]
    else:
        return data

# --- [ API MAP ] ---
API_MAP = {
    "📞 Number V1": "https://sbsakib.eu.cc/apis/num_v1?key=Demo&num={q}",
    "🚀 Number V3": "https://sbsakib.eu.cc/apis/num_v3?key=Demo&Info={q}",
    "🔍 Truecaller Pro": "https://rohittruecallerapi.vercel.app/info?number={q}",
    "📧 Email Info": "https://rohitemailapi.vercel.app/info?mail={q}",
    "🌐 Web Scrape": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
    "🆔 Aadhaar Info": "https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id={q}",
    "👨‍👩‍👧 Family Info": "https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term={q}",
    "🚗 Vehicle RC": "https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc={q}",
    "📸 Instagram": "https://sbsakib.eu.cc/apis/insta_info?key=Demo&username={q}",
    "🆔 TG User": "https://sbsakib.eu.cc/apis/tg_username?key=Demo&username={q}",
    "🆔 TG ID": "https://sbsakib.eu.cc/apis/tg_id?key=Demo&term={q}",
    "📍 Pincode": "https://sbsakib.eu.cc/apis/pincode?key=Demo&code={q}",
    "🏦 IFSC Code": "https://sbsakib.eu.cc/apis/ifsc?key=Demo&code={q}",
    "🌐 IP Info": "https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip={q}",
    "🎮 Free Fire": "https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid={q}",
}

# --- [ TRIPLE BACKUP LIST ] ---
NUMBER_BACKUPS = [
    "https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}",
    "https://ayaanmods.site/mobile.php?key=annonymousmobile&term={q}",
    "https://yash-code-ai-free-api.alphamovies.workers.dev/?number={q}"
]

user_states = {}

# --- [ START ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    banner = "**💎 MULTI LOOKUP OSINT BOT 💎**"
    buttons = [
        ["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"],
        ["🌐 Web Scrape", "🚗 Vehicle RC"], ["🆔 Aadhaar Info", "👨‍👩‍👧 Family Info"],
        ["📸 Instagram", "🆔 TG User"], ["🆔 TG ID", "📍 Pincode"],
        ["🏦 IFSC Code", "🎮 Free Fire"], ["👤 My Profile"]
    ]
    if user_id == ADMIN_ID: buttons.append(["📊 Admin Panel"])
    await message.reply_text(banner, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

# --- [ ADMIN PANEL STATS & BROADCAST ] ---
@app.on_message(filters.text & filters.user(ADMIN_ID) & filters.regex("^📊 Admin Panel$|^📢 Broadcast$|^🔙 Back$"))
async def admin_panel(client, message):
    if message.text == "📊 Admin Panel":
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM users WHERE status='banned'")
        banned = cursor.fetchone()[0]
        stats = f"🛡 **ADMIN PANEL**\n\n👥 Total: `{total}`\n🚫 Banned: `{banned}`\n✅ Active: `{total - banned}`"
        await message.reply_text(stats, reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "🔙 Back"]], resize_keyboard=True))
    elif message.text == "📢 Broadcast":
        user_states[ADMIN_ID] = "WAITING_FOR_BROADCAST"
        await message.reply_text("Send broadcast message:", reply_markup=ForceReply(selective=True))
    elif message.text == "🔙 Back":
        await start(client, message)

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start", "addcredits", "ban", "unban"]))
async def main_handler(client, message):
    user_id = message.from_user.id
    text = message.text

    # Admin Broadcast Capture
    if user_id == ADMIN_ID and user_states.get(user_id) == "WAITING_FOR_BROADCAST":
        cursor.execute("SELECT user_id FROM users")
        all_users = cursor.fetchall()
        for u in all_users:
            try: await client.send_message(u[0], text)
            except: pass
        del user_states[user_id]
        return await message.reply_text("✅ Broadcast Sent!")

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or (user[3] == 'banned' and user_id != ADMIN_ID): return

    if text == "👤 My Profile":
        c = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 Profile\n💰 Credits: `{c}`\n🔎 Total: `{user[2]}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for {text}:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching...**")
        
        # Log
        await client.send_message(LOG_CHANNEL, f"📢 **Request**\n👤 {message.from_user.first_name}\n🆔 `{user_id}`\n🛠 {service}\n📝 `{text}`")

        res_data = None
        try:
            # Main API
            resp = requests.get(API_MAP[service].format(q=text), timeout=10).json()
            
            # Triple Backup Logic for Numbers
            if "Number" in service and ("limit" in str(resp).lower() or "error" in str(resp).lower() or not resp.get("data")):
                for backup_url in NUMBER_BACKUPS:
                    try:
                        resp = requests.get(backup_url.format(q=text), timeout=10).json()
                        if resp and "error" not in str(resp).lower():
                            break
                    except: continue
            res_data = resp
        except: pass

        if res_data:
            pretty = json.dumps(clean_response(res_data), indent=4, ensure_ascii=False)
            await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```")
            cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,)) if user_id != ADMIN_ID else cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        else:
            await status.edit("❌ No data found in Main or Backup APIs.")
        del user_states[user_id]

# --- [ ADMIN COMMANDS ] ---
@app.on_message(filters.command(["addcredits", "ban", "unban"]) & filters.user(ADMIN_ID))
async def admin_cmds(client, message):
    cmd = message.command[0].lower()
    try:
        uid = int(message.command[1])
        if cmd == "addcredits":
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(message.command[2]), uid))
            await message.reply_text(f"💰 Credits added to `{uid}`")
        elif cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
            await message.reply_text(f"🚫 `{uid}` Banned.")
        db.commit()
    except: await message.reply_text("❌ Usage: `/cmd ID Amt`")

app.run()
    
