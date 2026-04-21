import os, requests, json, sqlite3
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup
from pyrogram.enums import ParseMode

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
LOG_CHANNEL = ADMIN_ID 

app = Client("multi_osint_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ CLEANER FUNCTION ] ---
def clean_response(data):
    # Branding hatane ke liye
    banned_keys = ["owner", "developer", "channel", "credit", "link", "by", "website", "api_by", "success", "status"]
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k.lower() not in banned_keys}
    elif isinstance(data, list):
        return [clean_response(i) for i in data]
    else:
        return data

# --- [ API MAP ] ---
API_MAP = {
    "📞 Number": "https://sbsakib.eu.cc/apis/num_v1?key=Demo&num={q}",
    "🆔 Aadhaar Info": "https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id={q}",
    "👨‍👩‍👧 Family Details": "https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term={q}",
    "📞 Truecaller": "https://sbsakib.eu.cc/apis/truecaller?key=Demo&num={q}",
    "🚗 Vehicle": "https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc={q}",
    "📸 Insta": "https://sbsakib.eu.cc/apis/insta_info?key=Demo&username={q}",
    "🆔 TG User": "https://sbsakib.eu.cc/apis/tg_username?key=Demo&username={q}",
    "🆔 TG ID": "https://sbsakib.eu.cc/apis/tg_id?key=Demo&term={q}",
    "📍 Pincode": "https://sbsakib.eu.cc/apis/pincode?key=Demo&code={q}",
    "🏦 IFSC": "https://sbsakib.eu.cc/apis/ifsc?key=Demo&code={q}",
    "🌐 IP Info": "https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip={q}",
    "🎮 Free Fire": "https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid={q}",
}

user_states = {}

# --- [ START COMMAND ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    # OSINT Banner and Welcome
    welcome_text = (
        "**╔══════════════════╗**\n"
        "** MULTI LOOKUP OSINT    **\n"
        "**╚══════════════════╝**\n\n"
        f"👋 **Welcome {message.from_user.first_name}**\n"
        "Aapka swagat hai sabse fast OSINT bot mein.\n\n"
        "Select a tool from below:"
    )
    
    keyboard = ReplyKeyboardMarkup([
        ["📞 Number", "🆔 Aadhaar Info"], ["👨‍👩‍👧 Family Details", "📞 Truecaller"],
        ["🆔 TG User", "🆔 TG ID"], ["🚗 Vehicle", "📍 Pincode"],
        ["🏦 IFSC", "🌐 IP Info"], ["🎮 Free Fire", "📸 Insta"],
        ["🎨 AI Image", "👤 My Profile"], ["📊 Admin Panel"]
    ], resize_keyboard=True)
    
    await message.reply_text(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

# --- [ ADMIN COMMANDS ] ---
@app.on_message(filters.command(["ban", "unban", "addcredits"]) & filters.user(ADMIN_ID))
async def admin_cmds(client, message):
    cmd = message.command[0]
    try:
        uid = int(message.command[1])
        if cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
            await message.reply_text(f"🚫 User `{uid}` banned.")
        elif cmd == "unban":
            cursor.execute("UPDATE users SET status='active' WHERE user_id=?", (uid,))
            await message.reply_text(f"✅ User `{uid}` unbanned.")
        elif cmd == "addcredits":
            amt = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, uid))
            await message.reply_text(f"💰 Added `{amt}` credits to `{uid}`.")
        db.commit()
    except:
        await message.reply_text("Format: `/cmd [ID] [Amount]`")

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or user[3] == 'banned': return

    # Admin Dashboard
    if text == "📊 Admin Panel" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        return await message.reply_text(f"🛡 **Admin Panel**\n\nUsers: `{total}`\n\nCommands:\n`/ban ID`\n`/unban ID`\n`/addcredits ID Amt`")

    # Profile
    if text == "👤 My Profile":
        cred_text = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **My Profile**\n\n💰 Credits: `{cred_text}`\n🔎 Total Searches: `{user[2]}`")

    # Service Selection
    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send input for **{text}**:")

    # Lookup Execution
    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching Raw Data...**")
        
        # Admin Logs
        log_msg = f"📢 **New Request Log**\n👤 Name: {message.from_user.first_name}\n🆔 User ID: `{user_id}`\n🛠 Tool: {service}\n📝 Query: `{text}`"
        try: await client.send_message(LOG_CHANNEL, log_msg)
        except: pass

        try:
            res = requests.get(API_MAP[service].format(q=text)).json()
            clean_res = clean_response(res)
            pretty_json = json.dumps(clean_res, indent=4, ensure_ascii=False)
            
            # Final Green Box Output
            await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty_json}\n```", parse_mode=ParseMode.MARKDOWN)
            
            # Credit Deduction Logic
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            else:
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        except:
            await status.edit("❌ API Error: Data not found.")
        del user_states[user_id]

app.run()
