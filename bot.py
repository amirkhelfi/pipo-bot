import asyncio, os, time, random, datetime, re, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights

API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAGC_GviR84bM0kl3Zmp4Ek9Okq56C9tWJM'
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688

GROUPS_FILE = "groups.json"
ADMINS_FILE = "admins.json"
WARNINGS_FILE = "warnings.json"

DEFAULT_ADMINS = [6941580330]

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except: pass
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

# --- المجموعات المفعلة ---
active_groups = set(load_json(GROUPS_FILE, []))
def save_groups():
    save_json(GROUPS_FILE, list(active_groups))

# --- المسؤولين ---
admins = load_json(ADMINS_FILE, DEFAULT_ADMINS)
def is_admin(sender):
    return sender.username == DEVELOPER_USERNAME or sender.id in admins

# --- التحذيرات ---
warnings_data = defaultdict(list, load_json(WARNINGS_FILE, {}))
def save_warnings():
    save_json(WARNINGS_FILE, warnings_data)

mute_status = {}
message_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
client = TelegramClient('bot', API_ID, API_HASH)

BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلب|قلبوز)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'ن\s*م\s*ي',
]
LINK_PATTERNS = [r'https?://\S+', r't\.me/\S+', r'www\.\S+']

def contains_swear(t): return any(re.search(p, t, re.I) for p in BAD_WORDS) if t else False
def contains_link(t): return any(re.search(p, t, re.I) for p in LINK_PATTERNS) if t else False
def is_forward(m): return bool(m.forward)

async def mute_user(chat, user, dur):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=datetime.datetime.fromtimestamp(time.time()+dur), send_messages=True)))
        return True
    except: return False
async def unmute_user(chat, user):
    try:
        await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, send_messages=False)))
        return True
    except: return False

# --- الأوامر العامة ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    if sender.username == DEVELOPER_USERNAME:
        await event.reply("⚡ **PIPO BOT** ⚡\n👑 المطور", buttons=[
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]
        ])
    else:
        await event.reply("ياحييي داصرتوني ثم ثم 😒💋")

@client.on(events.NewMessage(pattern='/تفعيل'))
async def activate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.add(event.chat_id)
    save_groups()
    await event.reply("✅ تم تفعيل البوت في هذه المجموعة.")

@client.on(events.NewMessage(pattern='/تعطيل'))
async def deactivate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.discard(event.chat_id)
    save_groups()
    await event.reply("❌ تم تعطيل البوت في هذه المجموعة.")

@client.on(events.NewMessage(pattern='/المجموعات'))
async def list_groups(event):
    if not is_admin(await event.get_sender()): return
    if not active_groups:
        return await event.reply("لا توجد مجموعات مفعلة.")
    txt = "📋 **المجموعات المفعلة:**\n"
    for gid in active_groups:
        try:
            entity = await client.get_entity(gid)
            txt += f"• {entity.title} ({gid})\n"
        except:
            txt += f"• {gid}\n"
    await event.reply(txt)

@client.on(events.NewMessage(pattern='/حب'))
async def love_calc(event):
    args = event.raw_text.split()
    if event.is_reply:
        target = await (await event.get_reply_message()).get_sender()
        user1 = (await event.get_sender()).first_name
        user2 = target.first_name if target else "???"
    elif len(args) >= 3:
        user1, user2 = args[1], args[2]
    else:
        return await event.reply("❌ استخدم: /حب @username أو بالرد على شخص.")
    percent = random.randint(50, 100)
    emojis = ["💔", "💖", "💘", "💕", "💓"]
    await event.reply(f"{user1} + {user2} = {random.choice(emojis)} {percent}%")

@client.on(events.NewMessage(pattern='/سر'))
async def anonymous(event):
    text = event.raw_text[5:].strip()
    if not text:
        return await event.reply("❌ اكتب رسالة بعد الأمر، مثال: `/سر هذا سر`")
    await event.delete()
    await asyncio.sleep(1)
    await client.send_message(event.chat_id, f"📩 رسالة مجهولة: {text}")

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def perm_mute(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time()+ten_years, 'name': target.first_name}
    await event.reply(f"🚫 هاك الكتمة يا {target.first_name} 😂")

@client.on(events.NewMessage(pattern='/تحذير'))
async def warn(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    uid = target.id; name = target.first_name or "لا اسم"
    warnings_data[uid].append(time.time())
    save_warnings()
    cur = len(warnings_data[uid])
    await event.reply(f"⚠️ {name} تحذير {cur}/3")
    if cur >= 3:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': time.time()+mute_duration, 'name': name}
            await event.reply(f"🚫 {name} كتم {mute_duration//60} د")
            del warnings_data[uid]; save_warnings()

@client.on(events.NewMessage(pattern='/مساعدة'))
async def help_cmd(event):
    await event.reply("📜 اختر فئة الأوامر:", buttons=[
        [Button.inline("👤 الأعضاء", b"help_member")],
        [Button.inline("🛡️ المسؤول", b"help_admin")],
    ])

@client.on(events.CallbackQuery)
async def callback(event):
    data = event.data.decode('utf-8')
    if data == "help_admin":
        await event.edit("🛡️ أوامر المسؤول:\n/قفل /فك /كتم /تحذير /تفعيل /تعطيل /مساعدة")
    elif data == "help_member":
        await event.edit("👤 أوامر الأعضاء:\n/start /حب /سر /مساعدة")
    elif data == "mute_dur":
        await event.reply(f"⏰ {mute_duration//60} د")
    elif data == "bot_stat":
        await event.reply(f"📊 مكتوم: {len(mute_status)}")
    elif data == "get_id":
        await event.reply(f"🆔 {event.chat_id}")
    elif data == "unmute_all_btn":
        for u in list(mute_status.keys()):
            try: await unmute_user(event.chat_id, u); del mute_status[u]
            except: pass
        await event.reply("🔓 فك الكل")

# --- الحماية (تعمل في جميع المجموعات المفعلة) ---
@client.on(events.NewMessage())
async def global_handler(event):
    if not event.is_group or not event.raw_text or event.out: return
    chat = event.chat_id
    if chat not in active_groups: return
    sender = await event.get_sender()
    if not sender or sender.id == (await client.get_me()).id: return
    if sender.username == DEVELOPER_USERNAME: return
    message_count[sender.id] += 1
    text = event.raw_text.strip()
    if link_protection and contains_link(text):
        await event.delete()
    elif forward_protection and is_forward(event.message):
        await event.delete()
    elif contains_swear(text.lower()):
        now = time.time(); uid = sender.id; name = sender.first_name or "مجهول"
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        if await mute_user(chat, uid, mute_duration):
            mute_status[uid] = {'until': now + mute_duration, 'name': name}
            await event.respond(f"🚫 {name} كتم {mute_duration//60} د")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(f"✅ PIPO BOT يعمل في {len(active_groups)} مجموعات")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
