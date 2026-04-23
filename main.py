import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021"))
LOG_CHANNEL = ADMIN_ID 

app = Client("soul_chaser_ghost", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ THE ULTIMATE GHOST CLEANER ] ---
def ghost_clean(data):
    # 1. Ye keys jahan bhi dikhein, delete kar do
    banned_keys = ["owner", "owners", "developer", "developers", "api_dev", "api_updates", "credit", "credits", "success", "msg", "status", "link", "website"]
    # 2. In words wali koi bhi VALUE delete kar do (Dev Usernames etc)
    banned_vals = ["@", "http", "t.me", "buy", "access", "dm", "sakib", "rohit", "froxtdevil", "kon_hu_mai"]

    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            # Key check
            if k.lower() in banned_keys: continue
            # Value string check
            if isinstance(v, str):
                v_low = v.lower()
                if any(word in v_low for word in banned_vals): continue
            
            cleaned_v = ghost_clean(v)
            if cleaned_v is not None:
                new_dict[k] = cleaned_v
        return new_dict if new_dict else None
    elif isinstance(data, list):
        new_list = [ghost_clean(i) for i in data if ghost_clean(i) is not None]
        return new_list if new_list else None
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
    "🎮 Free Fire": "https://sbsakib.eu.cc/apis/ff-info?key=Demo&uid={q}",
}

user_states = {}

# --- [ 1. PRIORITY ADMIN COMMANDS ] ---
# Ye filters ab buttons se pehle trigger honge
@app.on_message(filters.command(["addcredits", "ban", "unban"]) & filters.user(ADMIN_ID))
async def admin_cmds(client, message):
    try:
        cmd = message.command[0].lower()
        uid = int(message.command[1])
        if cmd == "addcredits":
            amt = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, uid))
            res = f"✅ `{amt}` Credits added to `{uid}`"
        elif cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
            res = f"🚫 User `{uid}` Banned."
        elif cmd == "unban":
            cursor.execute("UPDATE users SET status='active' WHERE user_id=?", (uid,))
            res = f"🔓 User `{uid}` Unbanned."
        db.commit()
        await message.reply_text(res)
    except:
        await message.reply_text("❌ Format: `/addcredits ID Amt` or `/ban ID`")

# --- [ 2. START & BUTTONS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    kb = [
        ["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"],
        ["🌐 Web Scrape", "🆔 Aadhaar Info"], ["🎮 Free Fire", "👤 My Profile"]
    ]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    await message.reply_text("**💎 SOUL CHASER OSINT 💎**", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

# --- [ 3. MAIN LOGIC ] ---
@app.on_message(filters.text & ~filters.command(["start", "addcredits", "ban", "unban"]))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # Admin Panel View
    if text == "📊 Admin Panel" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        return await message.reply_text(f"📊 **STATS**\nTotal Users: `{total}`\n\nUse `/addcredits` or `/ban` commands.")

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
        
        # Log to Channel
        await client.send_message(LOG_CHANNEL, f"📢 **Request**\n👤 {message.from_user.first_name}\n🆔 `{user_id}`\n🛠 {service}\n📝 `{text}`")

        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            # Hardcore Clean
            clean_res = ghost_clean(r)
            
            if clean_res:
                pretty = json.dumps(clean_res, indent=4, ensure_ascii=False)
                await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```")
                
                # DB Update
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,)) if user_id != ADMIN_ID else cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
            else:
                await status.edit("❌ Result not found or hidden by filter.")
        except: await status.edit("❌ API Error.")
        del user_states[user_id]

app.run()
        
