import os
import requests
import json
import sqlite3
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- [ CONFIGURATION FROM ENVIRONMENT VARIABLES ] ---
# Railway ke dashboard mein ye Variables zaroor set karna
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

app = Client("lookup_bot_pro", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DATABASE SETUP ] ---
# Railway Volume use kar rahe ho toh path change kar sakte ho
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
    (user_id INTEGER PRIMARY KEY, credits INTEGER, total_searches INTEGER, status TEXT, referred_by INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS history 
    (user_id INTEGER, query TEXT, service TEXT)''')
db.commit()

# --- [ KEYBOARD LAYOUT ] ---
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["📞 Number", "🆔 Aadhaar Info"],
        ["👨‍👩‍👧 Family Details", "📞 Truecaller"],
        ["🆔 TG User", "🆔 TG ID"],
        ["🚗 Vehicle", "📍 Pincode"],
        ["🏦 IFSC", "🌐 IP Info"],
        ["🎮 Free Fire", "📸 Insta"],
        ["🎨 AI Image", "👤 My Profile"],
        ["📊 Admin Panel"]
    ], resize_keyboard=True
)

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

# --- [ START COMMAND & REFERRAL ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    ref_by = int(message.command[1]) if len(message.command) > 1 else None
    
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # New User: 5 Credits
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, 5, 0, "active", ref_by))
        if ref_by:
            cursor.execute("UPDATE users SET credits = credits + 10 WHERE user_id=?", (ref_by,))
            try: await client.send_message(ref_by, "🎁 **Bonus!** Aapke link se koi join hua, 10 Credits add ho gaye.")
            except: pass
        db.commit()
    
    await message.reply_text(
        f"🔥 **INFO BOT PERSONAL ACTIVE**\n\nWelcome {message.from_user.first_name}!\nAapko 5 FREE Credits mile hain.",
        reply_markup=MAIN_KEYBOARD
    )

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text)
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text
    
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user or user[3] == "banned":
        return await message.reply_text("❌ Aap is bot se banned hain.")

    # --- My Profile ---
    if text == "👤 My Profile":
        bot_username = (await client.get_me()).username
        ref_link = f"https://t.me/{bot_username}?start={user_id}"
        cursor.execute("SELECT service, query FROM history WHERE user_id=? ORDER BY ROWID DESC LIMIT 3", (user_id,))
        hist = cursor.fetchall()
        h_text = "\n".join([f"• {h[0]}: `{h[1]}`" for h in hist]) if hist else "No history yet."
        
        return await message.reply_text(
            f"👤 **MY PROFILE**\n\n"
            f"💰 **Credits:** `{user[1]}`\n"
            f"🔎 **Total Searches:** `{user[2]}`\n\n"
            f"📜 **Recent History:**\n{h_text}\n\n"
            f"🔗 **Refer & Earn (10 Credits):**\n`{ref_link}`"
        )

    # --- Admin Panel ---
    if text == "📊 Admin Panel":
        if user_id != ADMIN_ID: return
        cursor.execute("SELECT COUNT(*) FROM users")
        total_u = cursor.fetchone()[0]
        return await message.reply_text(
            f"👨‍💻 **ADMIN PANEL**\n\nTotal Users: {total_u}\n\n"
            f"Commands:\n`/ban ID`\n`/unban ID`\n`/addcredit ID Amount`"
        )

    # --- Lookup Logic ---
    if text in API_MAP:
        if user[1] < 1:
            return await message.reply_text("❌ Credits khatam! Refer karke earn karein.")
        user_states[user_id] = text
        return await message.reply_text(f"📝 **Enter details for {text}:**")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 **Searching Raw JSON...**")
        
        try:
            url = API_MAP[service].format(q=text)
            r = requests.get(url).json()
            
            if r:
                raw_json = json.dumps(r, indent=4, ensure_ascii=False)
                await status.edit(f"✅ **Success!**\n\n```json\n{raw_json}\n```")
                
                # Update DB
                cursor.execute("UPDATE users SET credits = credits - 1, total_searches = total_searches + 1 WHERE user_id=?", (user_id,))
                cursor.execute("INSERT INTO history VALUES (?, ?, ?)", (user_id, text, service))
                db.commit()
            else:
                await status.edit("❌ Data nahi mila.")
        except:
            await status.edit("❌ API Error!")
        
        del user_states[user_id]

# --- Admin Commands ---
@app.on_message(filters.command("addcredit") & filters.user(ADMIN_ID))
async def add_c(client, message):
    cmd = message.text.split()
    cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (cmd[2], cmd[1]))
    db.commit()
    await message.reply_text(f"✅ {cmd[2]} Credits added to {cmd[1]}")

@app.on_message(filters.command("ban") & filters.user(ADMIN_ID))
async def ban_u(client, message):
    cursor.execute("UPDATE users SET status = 'banned' WHERE user_id=?", (message.command[1],))
    db.commit()
    await message.reply_text("🚫 User banned.")

app.run()
