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

app = Client("multi_lookup_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ CLEANER FUNCTION ] ---
def clean_response(data):
    banned_keys = ["owner", "developer", "channel", "credit", "link", "by", "website", "api_by", "success", "status", "msg"]
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
    
    banner = (
        "**╔══════════════════╗**\n"
        "** MULTI LOOKUP OSINT    **\n"
        "**╚══════════════════╝**"
    )
    
    # --- KEYBOARD LOGIC ---
    buttons = [
        ["📞 Number", "🆔 Aadhaar Info"], 
        ["👨‍👩‍👧 Family Details", "📞 Truecaller"],
        ["🆔 TG User", "🆔 TG ID"], 
        ["🚗 Vehicle", "📍 Pincode"],
        ["🏦 IFSC", "🌐 IP Info"], 
        ["🎮 Free Fire", "📸 Insta"],
        ["👤 My Profile"]
    ]
    
    # Agar Admin hai toh Admin Panel button add karo
    if user_id == ADMIN_ID:
        buttons.append(["📊 Admin Panel"])
    
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await message.reply_text(banner, reply_markup=keyboard)

# --- [ ADMIN LOGIC ] ---
@app.on_message(filters.text & filters.user(ADMIN_ID))
async def admin_panel_text(client, message):
    if message.text == "📊 Admin Panel":
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        msg = (
            "🛡 **ADMIN DASHBOARD**\n\n"
            f"Total Users: `{total}`\n\n"
            "**Commands:**\n"
            "`/ban ID` - User ban karne ke liye\n"
            "`/unban ID` - Unban karne ke liye\n"
            "`/addcredits ID Amt` - Credits dene ke liye"
        )
        return await message.reply_text(msg)

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
            amt = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, uid))
        db.commit()
        await message.reply_text("✅ Success!")
    except:
        await message.reply_text("Format galat hai!")

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text & ~filters.command(["start"]))
async def main_handler(client, message):
    user_id = message.from_user.id
    text = message.text

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user: return

    if user[3] == 'banned' and user_id != ADMIN_ID:
        return await message.reply_text("❌ Aap banned hain.")

    if text == "👤 My Profile":
        credits = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **Profile**\n💰 Credits: `{credits}`\n🔎 Total Searches: `{user[2]}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send input for **{text}**:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Raw Data Fetching...**")
        
        # Admin Logs
        log_msg = f"📢 **New Request Log**\n👤 Name: {message.from_user.first_name}\n🆔 ID: `{user_id}`\n🛠 Tool: {service}\n📝 Query: `{text}`"
        try: await client.send_message(LOG_CHANNEL, log_msg)
        except: pass

        try:
            res = requests.get(API_MAP[service].format(q=text)).json()
            clean_res = clean_response(res)
            pretty_json = json.dumps(clean_res, indent=4, ensure_ascii=False)
            
            # THE GREEN BOX FIX
            final_msg = f"**✅ {service} Result:**\n\n```json\n{pretty_json}\n```"
            await status.edit(final_msg, parse_mode=ParseMode.MARKDOWN)
            
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            else:
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        except:
            await status.edit("❌ No data found.")
        del user_states[user_id]

app.run()
