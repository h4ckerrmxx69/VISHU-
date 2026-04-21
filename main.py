import os, requests, json, sqlite3
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply
from pyrogram.enums import ParseMode

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
LOG_CHANNEL = ADMIN_ID # Yahan apna log channel ID daal sakte ho

app = Client("soul_chaser_supreme", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ NO BRANDING CLEANER ] ---
def clean_response(data):
    # 'owners' aur 'developers' jaise keys ko remove karne ke liye
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
    "🚀 Number V3": "https://sbsakib.eu.cc/apis/num_v3?key=Demo&Info={q}", # Nayi API Add ho gayi
    "🆔 Aadhaar Info": "https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id={q}",
    "👨‍👩‍👧 Family Info": "https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term={q}",
    "📞 Truecaller": "https://sbsakib.eu.cc/apis/truecaller?key=Demo&num={q}",
    "🚗 Vehicle RC": "https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc={q}",
    "📸 Instagram": "https://sbsakib.eu.cc/apis/insta_info?key=Demo&username={q}",
    "🆔 TG User": "https://sbsakib.eu.cc/apis/tg_username?key=Demo&username={q}",
    "🆔 TG ID": "https://sbsakib.eu.cc/apis/tg_id?key=Demo&term={q}",
    "📍 Pincode": "https://sbsakib.eu.cc/apis/pincode?key=Demo&code={q}",
    "🏦 IFSC Code": "https://sbsakib.eu.cc/apis/ifsc?key=Demo&code={q}",
    "🌐 IP Info": "https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip={q}",
    "🎮 Free Fire": "https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid={q}",
}

BACKUP_NUM_API = "https://ayaanmods.site/mobile.php?key=annonymousmobile&term={q}"
user_states = {}

# --- [ START COMMAND ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    banner = "**💎 SOUL CHASER SUPREME 💎**\nSelect a tool:"
    buttons = [
        ["📞 Number V1", "🚀 Number V3"], ["🆔 Aadhaar Info", "👨‍👩‍👧 Family Info"],
        ["📞 Truecaller", "🚗 Vehicle RC"], ["📸 Instagram", "🆔 TG User"],
        ["🆔 TG ID", "📍 Pincode"], ["🏦 IFSC Code", "🌐 IP Info"],
        ["🎮 Free Fire", "👤 My Profile"]
    ]
    if user_id == ADMIN_ID: buttons.append(["📊 Admin Panel"])
    await message.reply_text(banner, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

# --- [ ADMIN COMMANDS ] ---
@app.on_message(filters.command(["addcredits", "ban", "unban"]) & filters.user(ADMIN_ID))
async def admin_cmds(client, message):
    cmd = message.command[0].lower()
    try:
        target_id = int(message.command[1])
        if cmd == "addcredits":
            amount = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, target_id))
            text = f"✅ Added `{amount}` credits to `{target_id}`"
        elif cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (target_id,))
            text = f"🚫 User `{target_id}` banned."
        elif cmd == "unban":
            cursor.execute("UPDATE users SET status='active' WHERE user_id=?", (target_id,))
            text = f"🔓 User `{target_id}` unbanned."
        db.commit()
        await message.reply_text(text)
    except:
        await message.reply_text("❌ Usage: `/addcredits ID Amt` or `/ban ID`")

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["addcredits", "ban", "unban", "start"]))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text
    
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user: return
    if user[3] == 'banned' and user_id != ADMIN_ID:
        return await message.reply_text("❌ Aap is bot se banned hain.")

    if text == "📊 Admin Panel" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        return await message.reply_text(f"📊 **ADMIN PANEL**\n\nTotal Users: `{total}`\nAdmin Credits: `Unlimited`\n\n**Commands:**\n`/ban ID` | `/unban ID` | `/addcredits ID Amt`")

    if text == "👤 My Profile":
        c = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{c}`\n🔎 Total: `{user[2]}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"🌀 Send input for {text}:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching...**")
        
        # LOGGING REQUEST
        log_msg = (
            f"📢 **New Request Log**\n"
            f"👤 Name: {message.from_user.first_name}\n"
            f"🆔 User ID: `{user_id}`\n"
            f"🔗 Username: @{message.from_user.username}\n"
            f"🛠 Tool: {service}\n"
            f"📝 Query: `{text}`"
        )
        await client.send_message(LOG_CHANNEL, log_msg)

        try:
            res = requests.get(API_MAP[service].format(q=text), timeout=10).json()
            
            # Number Lookup Failover
            if "Number" in service and ("limit" in str(res).lower() or not res.get("data")):
                res = requests.get(BACKUP_NUM_API.format(q=text), timeout=10).json()
            
            pretty = json.dumps(clean_response(res), indent=4, ensure_ascii=False)
            await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```")
            
            # DB Update
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            else:
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        except: await status.edit("❌ Error: Result not found.")
        del user_states[user_id]

app.run()
