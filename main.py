import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5192884021")) 

app = Client("soul_chaser_ultra_final", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, credits INTEGER, searches INTEGER, status TEXT)")
db.commit()

# --- [ GHOST CLEANER: NO BRANDING ] ---
def ghost_clean(data):
    # Dev branding, links aur usernames ko result se gayab karne ke liye
    banned = ["owner", "owners", "developer", "developers", "api_dev", "api_updates", "credit", "credits", "dm", "buy", "access", "@", "http", "t.me", "sakib", "rohit", "froxtdevil", "kon_hu_mai"]
    
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k.lower() in banned: continue
            if isinstance(v, str) and any(word in v.lower() for word in banned): continue
            cleaned_v = ghost_clean(v)
            if cleaned_v is not None: new_dict[k] = cleaned_v
        return new_dict if new_dict else None
    elif isinstance(data, list):
        new_list = [ghost_clean(i) for i in data if ghost_clean(i) is not None]
        return new_list if new_list else None
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

# Number Backups
NUM_BACKUPS = [
    "https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}",
    "https://yash-code-ai-free-api.alphamovies.workers.dev/?number={q}"
]

# TG ID Backup (Jo tune bola)
TG_ID_BACKUP = "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}"

user_states = {}

# --- [ 1. ADMIN COMMANDS ] ---
@app.on_message(filters.command(["addcredits", "ban", "unban"]) & filters.user(ADMIN_ID))
async def admin_cmds(client, message):
    try:
        cmd = message.command[0].lower()
        uid = int(message.command[1])
        if cmd == "addcredits":
            amt = int(message.command[2])
            cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amt, uid))
            res = f"✅ Success! `{amt}` credits added to `{uid}`."
        elif cmd == "ban":
            cursor.execute("UPDATE users SET status='banned' WHERE user_id=?", (uid,))
            res = f"🚫 User `{uid}` Banned."
        db.commit()
        await message.reply_text(res)
    except:
        await message.reply_text("❌ Usage: `/addcredits ID Amount`")

# --- [ 2. ADMIN PANEL & BROADCAST ] ---
@app.on_message(filters.text & filters.user(ADMIN_ID) & filters.regex("^📊 Admin Panel$|^📢 Broadcast$|^➕ Add Credits$|^🔙 Back$"))
async def admin_panel_logic(client, message):
    if message.text == "📊 Admin Panel":
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        stats = f"🛡 **ADMIN PANEL**\n\n👥 Total Users: `{total}`\n💰 Admin: `Unlimited`"
        await message.reply_text(stats, reply_markup=ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🔙 Back"]], resize_keyboard=True))
    
    elif message.text == "➕ Add Credits":
        await message.reply_text("💡 Use command: `/addcredits (USER_ID) (AMOUNT)`")
    
    elif message.text == "📢 Broadcast":
        user_states[ADMIN_ID] = "WAIT_FOR_BC"
        await message.reply_text("📣 Send the message for broadcast:", reply_markup=ForceReply(selective=True))
    
    elif message.text == "🔙 Back":
        await start(client, message)

# --- [ 3. MAIN LOGIC ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users VALUES (?, 5, 0, 'active')", (user_id,))
        db.commit()
    
    kb = [
        ["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"],
        ["🆔 TG Username", "🆔 TG ID"], ["🆔 Aadhaar Info", "👨‍👩‍👧 Family Info"],
        ["🌐 Web Scrape", "🚗 Vehicle RC"], ["🎮 Free Fire", "👤 My Profile"]
    ]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

@app.on_message(filters.text & ~filters.command(["start", "addcredits", "ban", "unban"]))
async def main_handler(client, message):
    user_id = message.from_user.id
    text = message.text

    # Broadcast Logic
    if user_id == ADMIN_ID and user_states.get(user_id) == "WAIT_FOR_BC":
        cursor.execute("SELECT user_id FROM users")
        for u in cursor.fetchall():
            try: await client.send_message(u[0], text)
            except: continue
        del user_states[user_id]
        return await message.reply_text("✅ Broadcast complete!")

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user or (user[3] == 'banned' and user_id != ADMIN_ID): return

    if text == "👤 My Profile":
        c = "Unlimited" if user_id == ADMIN_ID else user[1]
        return await message.reply_text(f"👤 **PROFILE**\n💰 Credits: `{c}`\n🔎 Total Searches: `{user[2]}`")

    if text in API_MAP:
        if user_id != ADMIN_ID and user[1] < 1: return await message.reply_text("❌ No Credits!")
        user_states[user_id] = text
        return await message.reply_text(f"📝 Send Query for {text}:")

    if user_id in user_states:
        service = user_states[user_id]
        status = await message.reply_text("🔎 Searching...")
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            
            # --- [ BACKUP LOGIC ] ---
            # Number Backups
            if "Number" in service and ("limit" in str(r).lower() or not r.get("data")):
                for b_url in NUM_BACKUPS:
                    try:
                        r = requests.get(b_url.format(q=text), timeout=10).json()
                        if r and "data" in str(r): break
                    except: continue
            
            # TG ID Backup
            if service == "🆔 TG ID" and ("error" in str(r).lower() or not r):
                try:
                    r = requests.get(TG_ID_BACKUP.format(q=text), timeout=10).json()
                except: pass

            clean_res = ghost_clean(r)
            if clean_res:
                pretty = json.dumps(clean_res, indent=4, ensure_ascii=False)
                await status.edit(f"**✅ {service} Result:**\n\n```json\n{pretty}\n```")
                cursor.execute("UPDATE users SET credits = credits - 1, searches = searches + 1 WHERE user_id=?", (user_id,)) if user_id != ADMIN_ID else cursor.execute("UPDATE users SET searches = searches + 1 WHERE user_id=?", (user_id,))
                db.commit()
            else: await status.edit("❌ No clean data found.")
        except: await status.edit("❌ API Error. Try again later.")
        del user_states[user_id]

app.run()
    
