import asyncio, os, time, random, datetime, re, sys, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument

# ======== الإعدادات ========
API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8510476270:AAGMX1NjCg1n44vHJky3l1eUUQxR_W8Qckw'
GROUP_ID = -1003498206246
CHANNEL_1 = -1003878407748
CHANNEL_2 = -1003008879375
CHANNEL_3 = -1003498206246
DEVELOPER_USERNAME = 'amirx_xpipo'

PROTECTED_CHANNELS = [CHANNEL_1, CHANNEL_2, CHANNEL_3]

mute_status = {}
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False

WELCOME_MEDIA_DATA = None
WELCOME_MEDIA_TYPE = None
WELCOME_MEDIA_FILE = "welcome_media.json"
dev_media_mode = {}
DEV_VIDEO_DATA = None
DEV_VIDEO_FILE = "dev_video.json"

VOICE_URL = "https://files.catbox.moe/3z7q8w.mp3"

BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة)\b',
    r'(ني6|نق/ش|طي+ز|زب+|شر+موطة|قح+بة)',
]

LINK_PATTERNS = [
    r'https?://\S+', r'http?://\S+', r't\.me/\S+', r'telegram\.me/\S+', r'@\w+', r'www\.\S+',
    r'\S+\.com\b', r'\S+\.net\b', r'\S+\.org\b', r'\S+\.io\b', r'\S+\.app\b', r'\S+\.xyz\b',
    r'tiktok\.com', r'youtube\.com', r'youtu\.be', r'instagram\.com', r'facebook\.com', r'fb\.com',
    r'twitter\.com', r'x\.com', r'snapchat\.com', r'whatsapp\.com', r'wa\.me',
]

THE_ONLY_ROAST = "يا خو شحال تهدر بلع علينا فومك صدعتنا"

def get_welcome_message(name, user_id, username, group_title):
    now = datetime.datetime.now()
    join_date = now.strftime("%Y/%m/%d")
    join_time = now.strftime("%I:%M %p")
    return f"""—————— {group_title} —————
نورت قروبنا يا {name}!

اسمك: {name}
ايديك: {user_id}
يوزرك: @{username}

تاريخ انضمامك: {join_date}
الساعة: {join_time}

التزم بقوانين المجموعة
—————— {group_title} —————
"""

client = TelegramClient('bot', API_ID, API_HASH)
BOT_ID = None

def load_welcome_media():
    global WELCOME_MEDIA_DATA, WELCOME_MEDIA_TYPE
    try:
        if os.path.exists(WELCOME_MEDIA_FILE):
            with open(WELCOME_MEDIA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                WELCOME_MEDIA_TYPE = data.get('type')
                WELCOME_MEDIA_DATA = {'media_id': int(data.get('media_id', 0)), 'access_hash': int(data.get('access_hash', 0)), 'file_reference': data.get('file_reference', b'')}
                if WELCOME_MEDIA_DATA['media_id'] and WELCOME_MEDIA_DATA['access_hash']: return True
    except: pass
    return False

def load_dev_video():
    global DEV_VIDEO_DATA
    try:
        if os.path.exists(DEV_VIDEO_FILE):
            with open(DEV_VIDEO_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                DEV_VIDEO_DATA = {'media_id': int(data.get('media_id', 0)), 'access_hash': int(data.get('access_hash', 0)), 'file_reference': data.get('file_reference', b'')}
                if DEV_VIDEO_DATA['media_id'] and DEV_VIDEO_DATA['access_hash']: return True
    except: pass
    return False

async def save_dev_video(media):
    global DEV_VIDEO_DATA
    try:
        media_id = media.document.id; access_hash = media.document.access_hash; file_reference = media.document.file_reference or b''
        DEV_VIDEO_DATA = {'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}
        data = {'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}
        with open(DEV_VIDEO_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)
        load_dev_video()
        return True
    except: return False

async def send_dev_video(chat_id):
    try:
        file_reference = bytes.fromhex(DEV_VIDEO_DATA.get('file_reference', '')) if DEV_VIDEO_DATA.get('file_reference') else b''
        media = InputDocument(id=int(DEV_VIDEO_DATA['media_id']), access_hash=int(DEV_VIDEO_DATA['access_hash']), file_reference=file_reference)
        caption = f"""Dev @{DEVELOPER_USERNAME}
👑ℙ𝕚𝕡𝕠 ¹⁹
📍 Sétif"""
        await client.send_file(chat_id, media, caption=caption)
        return True
    except: return False

async def save_welcome_media(media, media_type):
    global WELCOME_MEDIA_DATA, WELCOME_MEDIA_TYPE
    try:
        WELCOME_MEDIA_TYPE = media_type
        if media_type == 'photo': media_id = media.id; access_hash = media.access_hash; file_reference = media.file_reference or b''
        else: media_id = media.document.id; access_hash = media.document.access_hash; file_reference = media.document.file_reference or b''
        WELCOME_MEDIA_DATA = {'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}
        data = {'type': media_type, 'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}
        with open(WELCOME_MEDIA_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)
        load_welcome_media()
        return True
    except: return False

async def send_welcome_media(chat_id, caption):
    try:
        file_reference = bytes.fromhex(WELCOME_MEDIA_DATA.get('file_reference', '')) if WELCOME_MEDIA_DATA.get('file_reference') else b''
        if WELCOME_MEDIA_TYPE == 'photo': media = InputPhoto(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=file_reference)
        else: media = InputDocument(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=file_reference)
        await client.send_file(chat_id, media, caption=caption)
        return True
    except: return False

async def send_with_bot_photo(chat_id, message, buttons=None):
    try:
        photos = await client.get_profile_photos('me', limit=1)
        if photos: await client.send_file(chat_id, photos[0], caption=message[:1024], buttons=buttons); return True
    except: pass
    try: await client.send_message(chat_id, message, buttons=buttons)
    except: pass
    return False

load_welcome_media()
load_dev_video()

def get_roast(name, username):
    violator_tag = f"@{username}" if username else name
    return f"""{THE_ONLY_ROAST}
المخالف: {violator_tag}
للاستفسار: @{DEVELOPER_USERNAME}
تم كتمك {mute_duration // 60} دقائق بسبب السب!"""

async def mute_user(chat_id, user_id, duration_seconds):
    try:
        rights = ChatBannedRights(until_date=datetime.datetime.fromtimestamp(time.time() + duration_seconds), send_messages=True)
        await client(EditBannedRequest(chat_id, user_id, rights)); return True
    except: return False

async def unmute_user(chat_id, user_id):
    try:
        rights = ChatBannedRights(until_date=None, send_messages=False)
        await client(EditBannedRequest(chat_id, user_id, rights)); return True
    except: return False

def contains_swear(text):
    if not text: return False
    for pattern in BAD_WORDS:
        if re.search(pattern, text, re.IGNORECASE): return True
    return False

def contains_link(text):
    if not text: return False
    for pattern in LINK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE): return True
    return False

def is_forward(msg): return bool(msg.forward)

async def delete_after_delay(message, delay=60):
    await asyncio.sleep(delay)
    try: await message.delete()
    except: pass

# ======== قفل وفتح يدوي ========
@client.on(events.NewMessage(pattern='/قفل_المجموعة'))
async def lock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked
    try:
        await client.edit_permissions(GROUP_ID, send_messages=False)
        chat_locked = True
        await event.reply(f"🔒 **تم قفل المجموعة يدوياً**\n👑 @{DEVELOPER_USERNAME}")
    except: pass

@client.on(events.NewMessage(pattern='/فك_القفل'))
async def unlock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked
    try:
        await client.edit_permissions(GROUP_ID, send_messages=True)
        chat_locked = False
        await event.reply(f"🔓 **تم فتح المجموعة يدوياً**\n👑 @{DEVELOPER_USERNAME}")
    except: pass

# ======== حماية الروابط والتوجيه ========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def protect_links_and_forwards(event):
    if not event.raw_text and not event.message: return
    if event.out: return
    sender = await event.get_sender()
    if sender and sender.id == BOT_ID: return
    if sender and sender.username == DEVELOPER_USERNAME: return
    msg = event.message; uid = sender.id; name = sender.first_name or "مجهول"
    if link_protection and event.raw_text and contains_link(event.raw_text):
        await event.delete()
        warn_msg = await event.reply(f"🚫 **{name}** ممنوع إرسال الروابط!\n👑 @{DEVELOPER_USERNAME}")
        asyncio.create_task(delete_after_delay(warn_msg, 10))
        return
    if forward_protection and is_forward(msg):
        await event.delete()
        warn_msg = await event.reply(f"🚫 **{name}** ممنوع التوجيه!\n👑 @{DEVELOPER_USERNAME}")
        asyncio.create_task(delete_after_delay(warn_msg, 10))
        return

@client.on(events.NewMessage(pattern='/تفعيل_حماية_الروابط'))
async def enable_link_protection(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = True
    await event.reply(f"✅ **تم تفعيل حماية الروابط**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_الروابط'))
async def disable_link_protection(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = False
    await event.reply(f"❌ **تم تعطيل حماية الروابط**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_التوجيه'))
async def enable_forward_protection(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = True
    await event.reply(f"✅ **تم تفعيل حماية التوجيه**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_التوجيه'))
async def disable_forward_protection(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = False
    await event.reply(f"❌ **تم تعطيل حماية التوجيه**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/حالة_الحماية'))
async def protection_status(event):
    await event.reply(f"""
🛡️ **حالة الحماية:**
🔗 الروابط: {'✅' if link_protection else '❌'}
↩️ التوجيه: {'✅' if forward_protection else '❌'}
🤬 السب: ✅
🔒 القفل: {'🔒 مقفول' if chat_locked else '🔓 مفتوح'}
👑 @{DEVELOPER_USERNAME}""")

# ======== ديديكاس ========
@client.on(events.NewMessage(pattern='/ديرلهم_ديديكاس'))
async def dedikas(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME:
        await event.reply(f"🚫 للمطور فقط! كلم @{DEVELOPER_USERNAME}")
        return
    await event.reply(f"ديديكاس لهاذو 🤣 فري مدرناش يا مطوري @{DEVELOPER_USERNAME}")

# ======== المطور ========
@client.on(events.NewMessage(pattern='/المطور'))
async def dev_info(event):
    if DEV_VIDEO_DATA:
        if await send_dev_video(event.chat_id): return
    await event.reply(f"""Dev @{DEVELOPER_USERNAME}
👑ℙ𝕚𝕡𝕠 ¹⁹
📍 Sétif""")

@client.on(events.NewMessage(pattern='/فيديو_المطور'))
async def set_dev_video(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'dev_video'
    await event.reply("📹 ارسل الفيديو في الخاص!")

@client.on(events.NewMessage(pattern='/احذف_كامل_الرسائل'))
async def delete_all_msgs(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return await event.reply(f"🚫 للمطور فقط!")
    if not event.is_private: return await event.reply("⚠️ للخاص فقط!")
    await event.reply("🗑️ جاري حذف كل رسائلي...")
    deleted, failed = 0, 0
    for chat_id in [GROUP_ID] + PROTECTED_CHANNELS:
        try:
            async for msg in client.iter_messages(chat_id, from_user='me', limit=None):
                try: await msg.delete(); deleted += 1; await asyncio.sleep(0.5)
                except: failed += 1
        except: pass
    await event.reply(f"✅ **تم الحذف!**\n🗑️ حذف: {deleted}\n❌ فشل: {failed}\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/ايدي'))
async def get_chat_id(event):
    await event.reply(f"Chat ID: `{event.chat_id}`")

# ======== ⭐ start - المطور فقط ⭐ ========
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME:
        return
    
    msg = f"""⚡ **PIPO BOT** ⚡
👑 **أهلاً مطوري @{DEVELOPER_USERNAME}**
📋 **لوحة التحكم:**"""
    buttons = [
        [Button.inline("🔇 مدة الكتم", b"mute_duration"), Button.inline("📊 حالة البوت", b"bot_status")],
        [Button.inline("🆔 معرفة الآيدي", b"get_id"), Button.inline("😂 ديديكاس", b"dedikas_cmd")],
        [Button.inline("🔓 فك كل الكمات", b"unmute_all_btn")],
    ]
    await send_with_bot_photo(event.chat_id, msg, buttons)

@client.on(events.CallbackQuery)
async def handle_buttons(event):
    data = event.data.decode('utf-8')
    if (await event.get_sender()).username != DEVELOPER_USERNAME:
        await event.answer("🚫 للمطور فقط!", alert=True)
        return
    if data == "mute_duration": await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق\n📝 `/مدة_الكتم رقم`")
    elif data == "bot_status":
        muted = len([u for u in mute_status if mute_status[u]['until'] > time.time()])
        await event.reply(f"📊 **حالة البوت**\n🔇 مكتوم: {muted}\n⏰ مدة الكتم: {mute_duration // 60} دقائق\n👑 @{DEVELOPER_USERNAME}")
    elif data == "get_id": await event.reply(f"🆔 Chat ID: `{event.chat_id}`")
    elif data == "dedikas_cmd": await event.reply(f"ديديكاس لهاذو 🤣 فري مدرناش يا مطوري @{DEVELOPER_USERNAME}")
    elif data == "unmute_all_btn":
        count = 0
        for uid in list(mute_status.keys()):
            try: await unmute_user(mute_status[uid].get('chat', GROUP_ID), uid); del mute_status[uid]; count += 1
            except: pass
        await event.reply(f"🔓 تم فك {count} كتم\n👑 @{DEVELOPER_USERNAME}")

# ======== حماية القنوات ========
@client.on(events.NewMessage(func=lambda e: e.is_channel))
async def channel_protect(event):
    try:
        chat_id = event.chat_id
        if chat_id not in PROTECTED_CHANNELS: return
        sender = await event.get_sender()
        if sender and sender.id == BOT_ID: return
        msg = event.message
        if msg.photo or msg.video or msg.document or msg.audio or msg.voice or msg.gif or msg.sticker: return
        uid = sender.id; name = sender.first_name or "مجهول"; now = time.time()
        if not contains_swear(msg.raw_text or ""): return
        await event.delete()
        await mute_user(chat_id, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'chat': chat_id, 'name': name}
        await client.send_message(chat_id, get_roast(name, sender.username))
    except: pass

# ======== فلترة المجموعة ========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def filter_bad(event):
    if not event.raw_text or event.out: return
    sender = await event.get_sender()
    if sender and sender.id == BOT_ID: return
    if not contains_swear(event.raw_text.lower()): return
    try:
        uid = sender.id; name = sender.first_name or "مجهول"; now = time.time()
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        await mute_user(event.chat_id, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'name': name}
        await event.reply(f"**{name}** مكتوم {mute_duration // 60} دقائق!\nالسبب: سب!\n@{DEVELOPER_USERNAME}")
    except: pass

# ======== ترحيب ========
@client.on(events.ChatAction())
async def welcome(event):
    if event.user_joined:
        user = await event.get_user()
        if not user.bot:
            await asyncio.sleep(3)
            try: chat = await event.get_chat(); group_title = chat.title
            except: group_title = "SUICIDE SQUAD"
            welcome_msg = get_welcome_message(name=user.first_name or "لاعب", user_id=user.id, username=user.username or "لايوجد", group_title=group_title)
            if WELCOME_MEDIA_DATA and WELCOME_MEDIA_TYPE:
                if await send_welcome_media(event.chat_id, welcome_msg): return
            await client.send_message(event.chat_id, welcome_msg)

@client.on(events.NewMessage(pattern='/فيديو_ترحيب'))
async def set_welcome_video(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'welcome'
    await event.reply("ارسل الفيديو او الصورة في الخاص لحفظه كترحيب!")

@client.on(events.NewMessage(func=lambda e: e.is_private and e.media))
async def handle_dev_media(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return
    media = event.media; media_type = None
    mode = dev_media_mode.get(sender.id, 'welcome')
    if mode == 'dev_video':
        if hasattr(media, 'document') and media.document and 'video' in media.document.mime_type.lower():
            if await save_dev_video(media): await event.reply("✅ تم حفظ فيديو المطور!")
        else: await event.reply("❌ ارسل فيديو فقط!")
        if sender.id in dev_media_mode: del dev_media_mode[sender.id]
        return
    if hasattr(media, 'photo') and media.photo: media_type = 'photo'
    elif hasattr(media, 'document') and media.document:
        if 'video' in media.document.mime_type.lower(): media_type = 'video'
        elif 'image' in media.document.mime_type.lower(): media_type = 'photo'
    if not media_type: return await event.reply("ارسل صورة او فيديو فقط!")
    if await save_welcome_media(media, media_type): await event.reply(f"✅ تم حفظ {media_type} الترحيب!")
    if sender.id in dev_media_mode: del dev_media_mode[sender.id]

@client.on(events.NewMessage(pattern=r'/مدة_الكتم (\d+)'))
async def set_mute_duration(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/مدة_الكتم'))
async def show_mute_duration(event):
    await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='/فك_كتم_(.+)'))
async def unmute_cmd(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    try:
        target = int(event.pattern_match.group(1))
        if target in mute_status:
            await unmute_user(mute_status[target].get('chat', GROUP_ID), target)
            name = mute_status[target].get('name', 'مجهول'); del mute_status[target]
            await event.reply(f"✅ تم فك الكتم عن {name}\n👑 @{DEVELOPER_USERNAME}")
        else: await event.reply("❌ غير مكتوم")
    except: pass

@client.on(events.NewMessage(pattern='/فك_كل_الكمات'))
async def unmute_all(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    count = 0
    for uid in list(mute_status.keys()):
        try: await unmute_user(mute_status[uid].get('chat', GROUP_ID), uid); del mute_status[uid]; count += 1
        except: pass
    await event.reply(f"✅ تم فك {count} كتم\n👑 @{DEVELOPER_USERNAME}")

# ======== ⭐ منع الخاص - رد واحد فقط ⭐ ========
@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_private(event):
    if event.out: return
    sender = await event.get_sender()
    if not sender: return
    if sender.username == DEVELOPER_USERNAME: return
    
    msg = f"🚫 الخاص مقفول!\n📩 ضفني إلى مجموعتك ورح أقوم بعملي 🛡️\n👑 المطور: @{DEVELOPER_USERNAME}"
    
    try:
        await client.send_file(event.chat_id, VOICE_URL, voice_note=True, caption=msg)
    except:
        try:
            await event.respond(msg)
        except:
            pass

# ======== ⭐ قفل تلقائي ⭐ ========
async def auto_lock_unlock():
    global chat_locked
    while True:
        now = datetime.datetime.now()
        hour, minute = now.hour, now.minute
        
        if hour == 23 and minute == 0 and not chat_locked:
            chat_locked = True
            try:
                await client.edit_permissions(GROUP_ID, send_messages=False)
                await client.send_message(GROUP_ID, f"""
╔══════════════════════════════╗
║     🔒 تـم إغـلاق الـمـجـمـوعـة 🔒     ║
╠══════════════════════════════╣
║  ⏰ الـسـاعـة: 12:00 لـيـلاً     ║
║  🌙 حـان وقـت الـنـوم           ║
║  🚫 تـم قـفـل الـدردشـة        ║
║  ⏳ يـعـاد فـتـحـهـا: 12:00 ظـهـراً ║
╠══════════════════════════════╣
║     🤖 PIPO BOT             ║
║     👑 @{DEVELOPER_USERNAME} ║
╚══════════════════════════════╝""")
            except: pass
        
        if hour == 11 and minute == 0 and chat_locked:
            chat_locked = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=True)
                await client.send_message(GROUP_ID, f"""
╔══════════════════════════════╗
║     🔓 تـم فـتـح الـمـجـمـوعـة 🔓     ║
╠══════════════════════════════╣
║  ⏰ الـسـاعـة: 12:00 ظـهـراً     ║
║  ☀️ صـبـاح الـخـيـر           ║
║  ✅ تـم فـتـح الـدردشـة        ║
║  💬 يمـكـنـكـم الإرسـال الآن     ║
╠══════════════════════════════╣
║     🤖 PIPO BOT             ║
║     👑 @{DEVELOPER_USERNAME} ║
╚══════════════════════════════╝""")
            except: pass
        
        await asyncio.sleep(30)

async def auto_unmute():
    while True:
        try:
            now = time.time()
            for uid in list(mute_status.keys()):
                if mute_status[uid]['until'] < now:
                    try: await unmute_user(mute_status[uid].get('chat', GROUP_ID), uid); del mute_status[uid]
                    except: pass
            await asyncio.sleep(30)
        except: await asyncio.sleep(30)

async def main():
    global BOT_ID
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    BOT_ID = me.id
    
    global chat_locked
    try:
        await client.edit_permissions(GROUP_ID, send_messages=True)
        chat_locked = False
    except: pass
    
    print(f"✅ PIPO BOT: @{me.username}")
    print(f"👑 @{DEVELOPER_USERNAME}")
    print(f"🎵 صوت I Love You للخاص")
    print(f"🌙 قفل: 23:00 UTC")
    print(f"☀️ فتح: 11:00 UTC")
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
