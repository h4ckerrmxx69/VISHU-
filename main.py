import os, requests, json, sqlite3
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove
from pyrogram.enums import ParseMode

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021")) # Direct apni ID yahan bhi daal sakte ho
LOG_CHANNEL = ADMIN_ID 

app = Client("multi_lookup_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

def clean_response(data):
    banned_keys = ["owner", "developer", "channel", "credit", "link", "by", "website", "api_by", "success", "status"]
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k.lower() not in banned_keys}
    elif isinstance(data, list):
        return [clean_response(i) for i in data]
    else:
        return data

API_MAP = {
    "📞 Number": "https://sbsakib.eu.cc/apis/num_v1?key=Demo&num={q}",
    "🆔 Aadhaar Info": "https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id={q}",
    "👨‍👩‍👧 Family Info": "https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term={q}",
    "📞 Truecaller": "https://sbsakib.eu.cc/apis/truecaller?key=Demo&num={q}",
    "🚗 Vehicle RC": "https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc={q}",
    "📸 Instagram": "https://sbsakib.eu.cc/apis/insta_info?key=Demo&username={q}",
    "🆔 TG Username": "https://sbsakib.eu.cc/apis/tg_username?key=Demo&username={q}",
    "🆔 TG ID": "https://sbsakib.eu.cc/apis/tg_id?key=Demo&term={q}",
    "📍 Pincode": "https://sbsakib.eu.cc/apis/pincode?key=Demo&code={q}",
    "🏦 IFSC Code": "https://sbsakib.eu.cc/apis/ifsc?key=Demo&code={q}",
    "🌐 IP Lookup": "https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip={q}",
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
    
    banner = (
        "**╔══════════════════╗**\n"
        "** MULTI LOOKUP OSINT BOT   **\n"
        "**╚══════════════════╝**"
    )
    
    # Keyboard Buttons
    btn_list = [
        ["📞 Number", "🆔 Aadhaar Info"],
        ["👨‍👩‍👧 Family Info", "📞 Truecaller"],
        ["🚗 Vehicle RC", "📸 Instagram"],
        ["🆔 TG Username", "🆔 TG ID"],
        ["📍 Pincode", "🏦 IFSC Code"],
        ["🌐 IP Lookup", "🎮 Free Fire"],
        ["👤 My Profile"]
    ]
    
    # Admin Check for Button
    if user_id == ADMIN_ID:
        btn_list.append(["📊 Admin Panel"])
        print(f"Admin Logged In: {user_id}") # Console check
    
    await message.reply_text(banner, reply_markup=ReplyKeyboardMarkup(btn_list, resize_keyboard=True))

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start"]))
async def handle_text(client, message):
    user_id = message.from_user.id
    text = message.text

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user: return

    # Ban Bypass for Admin
    if user[3] == 'banned' and user_id != ADMIN_ID:
        return await message.reply_text("❌ Aap is bot se banned hain.")

    # Admin Panel Toggle
    if text == "📊 Admin Panel" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        panel_text = (
            "🛡 **ADMIN PANEL**\n\n"
            f"Total Users: `{total}`\n"
            "Admin Credits: `Unlimited`\n\n"
            "**Commands:**\n"
            "`/ban ID` | `/unban ID` | `/addcredits ID Amt`"
        )
        return await message.reply_text(panel_text)

    if text == "👤 My Profile":
        c = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **Profile**\n💰 Credits: `{c}`\n🔎 Total: `{user[2]}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for **{text}**:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching...**")
        
        try:
            res = requests.get(API_MAP[service].format(q=text)).json()
            pretty = json.dumps(clean_response(res), indent=4, ensure_ascii=False)
            
            # THE GREEN BOX FIX (Markdown Mono)
            await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```", parse_mode=ParseMode.MARKDOWN)
            
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            else:
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        except:
            await status.edit("❌ Error: Result not found.")
        del user_states[user_id]

# --- [ ADMIN COMMAND HANDLER ] ---
@app.on_message(filters.command(["ban", "unban", "addcredits"]) & filters.user(ADMIN_ID))
async def admin_commands(client, message):
    cmd = message.command[0]
    try:
        uid = int(message.command[1])
        if cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
        elif cmd == "unban":
            cursor.execute("UPDATE users SET status='active' WHERE user_id=?", (uid,))
        elif cmd == "addcredits":
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(message.command[2]), uid))
        db.commit()
        await message.reply_text("✅ Done!")
    except:
        await message.reply_text("Format: `/cmd ID [Amt]`")

app.run()
        
