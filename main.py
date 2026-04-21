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

app = Client("lookup_bot_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ CLEANER FUNCTION ] ---
def clean_response(data):
    # Faltu branding hatane ke liye keywords
    banned_keys = ["owner", "developer", "channel", "credit", "link", "by", "website", "api_by", "success", "status"]
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k.lower() not in banned_keys}
    elif isinstance(data, list):
        return [clean_response(i) for i in data]
    else:
        return data

# --- [ API MAP ] ---
API_MAP = {
    "📞 Number": "[https://sbsakib.eu.cc/apis/num_v1?key=Demo&num=](https://sbsakib.eu.cc/apis/num_v1?key=Demo&num=){q}",
    "🆔 Aadhaar Info": "[https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id=](https://sbsakib.eu.cc/apis/aadhaar?key=Demo&id=){q}",
    "👨‍👩‍👧 Family Details": "[https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term=](https://sbsakib.eu.cc/apis/family_aadhaar?key=Demo&term=){q}",
    "📞 Truecaller": "[https://sbsakib.eu.cc/apis/truecaller?key=Demo&num=](https://sbsakib.eu.cc/apis/truecaller?key=Demo&num=){q}",
    "🚗 Vehicle": "[https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc=](https://sbsakib.eu.cc/apis/vehicle_num?key=Demo&rc=){q}",
    "📸 Insta": "[https://sbsakib.eu.cc/apis/insta_info?key=Demo&username=](https://sbsakib.eu.cc/apis/insta_info?key=Demo&username=){q}",
    "🆔 TG User": "[https://sbsakib.eu.cc/apis/tg_username?key=Demo&username=](https://sbsakib.eu.cc/apis/tg_username?key=Demo&username=){q}",
    "🆔 TG ID": "[https://sbsakib.eu.cc/apis/tg_id?key=Demo&term=](https://sbsakib.eu.cc/apis/tg_id?key=Demo&term=){q}",
    "📍 Pincode": "[https://sbsakib.eu.cc/apis/pincode?key=Demo&code=](https://sbsakib.eu.cc/apis/pincode?key=Demo&code=){q}",
    "🏦 IFSC": "[https://sbsakib.eu.cc/apis/ifsc?key=Demo&code=](https://sbsakib.eu.cc/apis/ifsc?key=Demo&code=){q}",
    "🌐 IP Info": "[https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip=](https://sbsakib.eu.cc/apis/ip_info?key=Demo&ip=){q}",
    "🎮 Free Fire": "[https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid=](https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid=){q}",
}

user_states = {}

@app.on_message(filters.text & ~filters.command(["start"]))
async def main_logic(client, message):
    user_id = message.from_user.id
    text = message.text
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or user[3] == 'banned': return

    if text in API_MAP:
        if user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send input for **{text}**:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching...**")
        
        # Admin Log Message
        log_text = (f"📢 **New Request Log**\n"
                    f"👤 **Name:** {user_name}\n"
                    f"🆔 **User ID:** `{user_id}`\n"
                    f"🔗 **Username:** {username}\n"
                    f"🛠 **Tool:** {service}\n"
                    f"📝 **Query:** `{text}`")
        try: await client.send_message(LOG_CHANNEL, log_text)
        except: pass

        try:
            raw_res = requests.get(API_MAP[service].format(q=text)).json()
            filtered_res = clean_response(raw_res)
            
            # JSON format with proper indentation
            pretty_json = json.dumps(filtered_res, indent=4, ensure_ascii=False)
            
            # Triple backticks for MarkdownV2 'Green Box' effect
            # .edit() me parse_mode dena zaroori hai
            response_text = f"**✅ {service} Result:**\n\n```json\n{pretty_json}\n```"
            
            await status.edit(response_text, parse_mode=ParseMode.MARKDOWN)
            
            cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        except Exception as e:
            await status.edit(f"❌ Error: Data not found.\n`{str(e)}`")
        
        del user_states[user_id]

app.run()
        
