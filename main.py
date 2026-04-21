import os, requests, json, sqlite3
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply
from pyrogram.enums import ParseMode

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
LOG_CHANNEL = ADMIN_ID 

app = Client("multi_lookup_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ STRICTOR CLEANER - NO BRANDING ] ---
def clean_response(data):
    # 'owners' aur 'developers' jaise plural keys ko bhi filter karta hai
    banned = [
        "owner", "owners", "developer", "developers", "channel", "credits", 
        "link", "by", "website", "api_by", "success", "status", "msg", "credit"
    ]
    if isinstance(data, dict):
        return {k: clean_response(v) for k, v in data.items() if k.lower() not in banned}
    elif isinstance(data, list):
        return [clean_response(i) for i in data]
    else:
        return data

# --- [ API MAP ] ---
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

# BACKUP API FOR NUMBER
BACKUP_NUM_API = "https://ayaanmods.site/mobile.php?key=annonymousmobile&term={q}"

user_states = {}

# --- [ START ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    banner = "**╔══════════════════╗**\n** MULTI LOOKUP OSINT BOT   **\n**╚══════════════════╝**"
    
    buttons = [
        ["📞 Number", "🆔 Aadhaar Info"], ["👨‍👩‍👧 Family Info", "📞 Truecaller"],
        ["🚗 Vehicle RC", "📸 Instagram"], ["🆔 TG Username", "🆔 TG ID"],
        ["📍 Pincode", "🏦 IFSC Code"], ["🌐 IP Lookup", "🎮 Free Fire"],
        ["👤 My Profile"]
    ]
    if user_id == ADMIN_ID: buttons.append(["📊 Admin Panel"])
    await message.reply_text(banner, reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

# --- [ ADMIN PANEL ] ---
@app.on_message(filters.text & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    if message.text == "📊 Admin Panel":
        await message.reply_text(
            "🛡 **ADMIN CONTROL**\n\nChoose an action:",
            reply_markup=ReplyKeyboardMarkup([["➕ Add Credits", "🚫 Ban User"], ["🔙 Back"]], resize_keyboard=True)
        )
    elif message.text == "➕ Add Credits":
        await message.reply_text("Send like this: `/addcredits 12345 100`", reply_markup=ForceReply(selective=True))
    elif message.text == "🚫 Ban User":
        await message.reply_text("Send ID: `/ban 12345`", reply_markup=ForceReply(selective=True))
    elif message.text == "🔙 Back":
        await start(client, message)

# --- [ ADMIN CMDS ] ---
@app.on_message(filters.command(["ban", "unban", "addcredits"]) & filters.user(ADMIN_ID))
async def admin_exe(client, message):
    cmd = message.command[0].lower()
    try:
        uid = int(message.command[1])
        if cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
            msg = f"🚫 `{uid}` banned."
        elif cmd == "addcredits":
            amt = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, uid))
            msg = f"💰 Added `{amt}` to `{uid}`."
        db.commit()
        await message.reply_text(msg)
    except: await message.reply_text("❌ Galat format!")

# --- [ MAIN HANDLER ] ---
@app.on_message(filters.text)
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or (user[3] == 'banned' and user_id != ADMIN_ID): return

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
        
        res_data = None
        try:
            # Main API Call
            resp = requests.get(API_MAP[service].format(q=text), timeout=10).json()
            
            # Agar Number search hai aur result galat/khali hai, toh backup chalao
            if service == "📞 Number" and ("message" in str(resp).lower() or not resp.get("data")):
                resp = requests.get(BACKUP_NUM_API.format(q=text), timeout=10).json()
            
            res_data = resp
        except:
            # Error aane par Number backup try karo
            if service == "📞 Number":
                try: res_data = requests.get(BACKUP_NUM_API.format(q=text), timeout=10).json()
                except: pass

        if res_data:
            pretty = json.dumps(clean_response(res_data), indent=4, ensure_ascii=False)
            await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```", parse_mode=ParseMode.MARKDOWN)
            
            if user_id != ADMIN_ID:
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,))
            else:
                cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
            db.commit()
        else:
            await status.edit("❌ No data found in Main or Backup API.")
        
        del user_states[user_id]

app.run()
                
