import os, requests, json, sqlite3, asyncio
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, ForceReply

# --- [ CONFIG ] ---
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5192884021 # Tera Fix ID

PROTECTED_IDS = [str(ADMIN_ID), "5192884021", "6011993446"] 

app = Client("soul_chaser_final_master", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- [ DB SETUP ] ---
db = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    credits INTEGER DEFAULT 5, 
    searches INTEGER DEFAULT 0, 
    status TEXT DEFAULT 'active', 
    referred_by INTEGER DEFAULT 0)""")
db.commit()

# --- [ FIXED API MAPPING ] ---
API_MAP = {
    "📞 Number V1": "https://ayaanmods.site/sms.php?key=annonymoussms&term={q}",
    "🚀 Number V3": "https://cyber-osint-num-infos.vercel.app/api/numinfo?key=Anonymous&num={q}",
    "🔍 Truecaller Pro": "https://rohittruecallerapi.vercel.app/info?number={q}",
    "📧 Email Info": "https://rohitemailapi.vercel.app/info?mail={q}",
    "🆔 TG ID": "https://ayaanmods.site/id.php?id={q}",
    "🚗 Vehicle RC": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
    "🌐 Web Scrape": "https://rohit-website-scrapper-api.vercel.app/zip?url={q}",
}

user_states = {}

# --- [ GHOST CLEANER LOGIC ] ---
def ghost_clean(data):
    # Jo bhi branding tujhe hatani hai, yahan daal de
    banned = ["owner", "developer", "api_dev", "api_updates", "credit", "dm", "buy", "access", "@", "http", "t.me", "sakib", "rohit", "froxtdevil", "ayaanmods"]
    if isinstance(data, dict):
        return {k: ghost_clean(v) for k, v in data.items() if not any(w in str(k).lower() for w in banned) and ghost_clean(v) is not None}
    elif isinstance(data, list):
        return [ghost_clean(i) for i in data if ghost_clean(i) is not None]
    elif isinstance(data, str):
        if any(w in data.lower() for w in banned):
            return None
    return data

# --- [ LOG SYSTEM ] ---
async def send_log(user, tool, query):
    log_text = (
        f"📢 **NEW REQUEST LOG**\n\n"
        f"👤 **User:** {user.first_name} ❤️\n"
        f"🆔 **ID:** `{user.id}`\n"
        f"🔗 **User:** @{user.username if user.username else 'None'}\n"
        f"🛠 **Tool:** `{tool}`\n"
        f"📝 **Query:** `{query}`"
    )
    try: await app.send_message(ADMIN_ID, log_text)
    except: pass

# --- [ KEYBOARDS ] ---
def get_main_kb(user_id):
    kb = [["📞 Number V1", "🚀 Number V3"], ["🔍 Truecaller Pro", "📧 Email Info"], ["🆔 TG ID", "🚗 Vehicle RC"], ["🌐 Web Scrape", "🎁 Refer & Earn"], ["👤 My Profile"]]
    if user_id == ADMIN_ID: kb.append(["📊 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_admin_kb():
    return ReplyKeyboardMarkup([["📢 Broadcast", "➕ Add Credits"], ["🚫 Ban User", "✅ Unban User"], ["🔙 Back"]], resize_keyboard=True)

# --- [ HANDLERS ] ---
@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    cursor.execute("SELECT status FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()

    if res and res[0] == "banned":
        return await message.reply_text("❌ Baap se panga nahi! Tu Banned hai. 😂🖕")

    if not res:
        ref_id = int(message.command[1]) if len(message.command) > 1 else 0
        if ref_id != 0 and ref_id != user_id:
            cursor.execute("UPDATE users SET credits = credits + 5 WHERE user_id=?", (ref_id,))
            try: await client.send_message(ref_id, "🎁 **Referral Bonus!** +5 Credits added.")
            except: pass
        cursor.execute("INSERT INTO users (user_id, status, referred_by) VALUES (?, 'active', ?)", (user_id, ref_id))
        db.commit()
    
    await message.reply_text("💎 **SOUL CHASER SUPREME** 💎\nNaye user ko 5 credits free mile hain!", reply_markup=get_main_kb(user_id))

@app.on_message(filters.text & ~filters.command("start"))
async def handle_all(client, message):
    user_id = message.from_user.id
    text = message.text

    # --- Admin Logic ---
    if user_id == ADMIN_ID:
        if text == "📊 Admin Panel":
            return await message.reply_text("🛡 **ADMIN CONTROLS**", reply_markup=get_admin_kb())
        elif text in ["📢 Broadcast", "➕ Add Credits", "🚫 Ban User", "✅ Unban User"]:
            user_states[user_id] = text
            return await message.reply_text(f"📝 Proceed with **{text}**:", reply_markup=ForceReply(selective=True))
        elif text == "🔙 Back":
            return await message.reply_text("💎 Main Menu", reply_markup=get_main_kb(user_id))

    # --- Admin Action Processing ---
    if user_id == ADMIN_ID and user_id in user_states:
        state = user_states.pop(user_id)
        if state == "📢 Broadcast":
            cursor.execute("SELECT user_id FROM users"); users = cursor.fetchall()
            for u in users:
                try: await client.send_message(u[0], f"📢 **ADMIN:**\n\n{text}"); await asyncio.sleep(0.05)
                except: pass
            return await message.reply_text("✅ Broadcast Done.", reply_markup=get_admin_kb())
        elif state == "➕ Add Credits":
            try:
                tid, amt = text.split()
                cursor.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (int(amt), int(tid))); db.commit()
                return await message.reply_text(f"✅ Credits Updated.", reply_markup=get_admin_kb())
            except: return await message.reply_text("❌ Error! ID AMOUNT", reply_markup=get_admin_kb())

    # --- Profile & Refer ---
    if text == "👤 My Profile":
        cursor.execute("SELECT credits, searches FROM users WHERE user_id=?", (user_id,))
        u = cursor.fetchone()
        return await message.reply_text(f"👤 **PROFILE**\n\n💰 Credits: `{u[0]}`\n🔎 Searches: `{u[1]}`", reply_markup=get_main_kb(user_id))

    if text == "🎁 Refer & Earn":
        bot = (await client.get_me()).username
        return await message.reply_text(f"🎁 **Refer & Earn**\nGet 5 credits per refer!\n\n🔗 `https://t.me/{bot}?start={user_id}`", reply_markup=get_main_kb(user_id))

    # --- Search Tools ---
    if text in API_MAP:
        cursor.execute("SELECT credits FROM users WHERE user_id=?", (user_id,))
        if cursor.fetchone()[0] < 1 and user_id != ADMIN_ID:
            return await message.reply_text("❌ Credits khatam! Refer karke earn karo.", reply_markup=get_main_kb(user_id))
        return await message.reply_text(f"📝 Send Query for {text}:", reply_markup=ForceReply(selective=True))

    # --- API Execution & Ghost Cleaner ---
    if message.reply_to_message and "Send Query for" in message.reply_to_message.text:
        service = message.reply_to_message.text.split("for ")[-1].strip(":")
        
        if any(pid in text for pid in PROTECTED_IDS):
            return await message.reply_text("Baap ka data mat nikal bsdk! 😂🖕", reply_markup=get_main_kb(user_id))

        await send_log(message.from_user, service, text)
        status = await message.reply_text("🔎 Searching...")
        
        try:
            r = requests.get(API_MAP[service].format(q=text), timeout=15).json()
            # ✨ Applying Ghost Cleaner ✨
            clean_res = ghost_clean(r)
            
            if clean_res:
                result_text = json.dumps(clean_res, indent=2, ensure_ascii=False)
                await status.edit(f"✅ **Result Found!**\n\n```json\n{result_text}\n```", reply_markup=get_main_kb(user_id))
                cursor.execute("UPDATE users SET searches = searches + 1, credits = credits - 1 WHERE user_id=?", (user_id,))
                db.commit()
            else:
                await status.edit("❌ No clean records found.", reply_markup=get_main_kb(user_id))
        except:
            await status.edit("❌ API Timeout or Error.", reply_markup=get_main_kb(user_id))

app.run()
