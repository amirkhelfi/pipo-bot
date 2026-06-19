import asyncio, os, time, random, datetime, re, sys, json, tempfile
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
DEVELOPER_ID = 8050958688
VIP_USERS = [6941580330, 8050958688]
PROTECTED_CHANNELS = [CHANNEL_1, CHANNEL_2, CHANNEL_3]

mute_status = {}
violation_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False
reminder_sent = False
last_muted_user = {}

WELCOME_MEDIA_DATA = None
WELCOME_MEDIA_TYPE = None
WELCOME_MEDIA_FILE = "welcome_media.json"
dev_media_mode = {}
DEV_VIDEO_DATA = None
DEV_VIDEO_FILE = "dev_video.json"

# ⭐⭐ كشف سب متطور ⭐⭐
BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلب|قلبوز)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'(ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪﻛﻚ6])',
    r'([كڪﻛﻚګگ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$])',
    r'([ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ])',
    r'([زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ])',
    r'([قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ])',
    r'(f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ])',
    r'([nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر])',
    r'\b(زبي|زبيي|كسك|طيزك|قحبتك|قحبتي)\b',
    r'\b(يا[\s]*ود[\s]*الكبدة|يا[\s]*ولد[\s]*القحبة|ولد[\s]*الزانية)\b',
    r'\b(نعل[\s]*الدين|نعل[\s]*الوالدين|نعل[\s]*الرب)\b',
    r'\b(الله[\s]*ينعل|الله[\s]*يلعن|ينعل[\s]*دين|يلعن[\s]*دين)\b',
    r'\b(ك\s*س|ك\s*ص|ط\s*ي\s*ز|ز\s*ب|ن\s*ي\s*ك|ق\s*ح\s*ب)\b',
    r'[كڪﻛﻚ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[سښصث]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[ببـپ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]?[كڪﻛﻚ]',
]

LINK_PATTERNS = [
    r'https?://\S+', r't\.me/\S+', r'www\.\S+',
    r'\S+\.com\b', r'\S+\.net\b', r'\S+\.org\b',
    r'tiktok\.com', r'youtube\.com', r'instagram\.com', r'facebook\.com',
]

def get_mute_message(name, username, duration):
    violator = f"@{username}" if username else name
    return f"""
╔══════════════════════════════╗
║     🚫 تـم كـتـم عـضـو 🚫       ║
╠══════════════════════════════╣
║  👤 {violator}
║  ⏰ {duration} دقـائـق
║  🤬 كـلـمـات مـمـنـوعـة
╠══════════════════════════════╣
║     👑 @{DEVELOPER_USERNAME}
╚══════════════════════════════╝
"""

def get_welcome_message(name, user_id, username, group_title):
    now = datetime.datetime.now()
    return f"—————— {group_title} —————\nنورت قروبنا يا {name}!\nاسمك: {name}\nايديك: {user_id}\nيوزرك: @{username}\nتاريخ: {now.strftime('%Y/%m/%d %I:%M %p')}\n—————— {group_title} —————"

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
        with open(DEV_VIDEO_FILE, 'w', encoding='utf-8') as f: json.dump({'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}, f)
        load_dev_video(); return True
    except: return False

async def send_dev_video(chat_id):
    try:
        file_reference = bytes.fromhex(DEV_VIDEO_DATA.get('file_reference', '')) if DEV_VIDEO_DATA.get('file_reference') else b''
        media = InputDocument(id=int(DEV_VIDEO_DATA['media_id']), access_hash=int(DEV_VIDEO_DATA['access_hash']), file_reference=file_reference)
        await client.send_file(chat_id, media, caption=f"Dev @{DEVELOPER_USERNAME}\n👑ℙ𝕚𝕡𝕠 ¹⁹\n📍 Sétif")
        return True
    except: return False

async def save_welcome_media(media, media_type):
    global WELCOME_MEDIA_DATA, WELCOME_MEDIA_TYPE
    try:
        WELCOME_MEDIA_TYPE = media_type
        if media_type == 'photo': media_id = media.id; access_hash = media.access_hash; file_reference = media.file_reference or b''
        else: media_id = media.document.id; access_hash = media.document.access_hash; file_reference = media.document.file_reference or b''
        WELCOME_MEDIA_DATA = {'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}
        with open(WELCOME_MEDIA_FILE, 'w', encoding='utf-8') as f: json.dump({'type': media_type, 'media_id': str(media_id), 'access_hash': str(access_hash), 'file_reference': file_reference.hex() if file_reference else ''}, f)
        load_welcome_media(); return True
    except: return False

async def send_welcome_media(chat_id, caption):
    try:
        file_reference = bytes.fromhex(WELCOME_MEDIA_DATA.get('file_reference', '')) if WELCOME_MEDIA_DATA.get('file_reference') else b''
        if WELCOME_MEDIA_TYPE == 'photo': media = InputPhoto(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=file_reference)
        else: media = InputDocument(id=int(WELCOME_MEDIA_DATA['media_id']), access_hash=int(WELCOME_MEDIA_DATA['access_hash']), file_reference=file_reference)
        await client.send_file(chat_id, media, caption=caption)
        return True
    except: return False

load_welcome_media()
load_dev_video()

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

# ======== الأوامر ========
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    if sender.username == DEVELOPER_USERNAME:
        buttons = [
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة البوت", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("😂 ديديكاس", b"dedikas_cmd")],
            [Button.inline("🔓 فك الكل", b"unmute_all_btn")],
        ]
        try:
            photos = await client.get_profile_photos('me', limit=1)
            if photos: await client.send_file(event.chat_id, photos[0], caption=f"⚡ **PIPO BOT** ⚡\n👑 @{DEVELOPER_USERNAME}", buttons=buttons); return
        except: pass
        await event.respond(f"⚡ **PIPO BOT** ⚡\n👑 @{DEVELOPER_USERNAME}", buttons=buttons)
    else:
        try: await event.react("❤️")
        except: pass

@client.on(events.NewMessage(pattern='/قفل_المجموعة'))
async def lock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked; chat_locked = True
    await client.edit_permissions(GROUP_ID, send_messages=False)
    await event.reply(f"🔒 تم قفل المجموعة\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/فك_القفل'))
async def unlock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked; chat_locked = False
    await client.edit_permissions(GROUP_ID, send_messages=True)
    await event.reply(f"🔓 تم فتح المجموعة\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/ديرلهم_ديديكاس'))
async def dedikas(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    await event.reply(f"ديديكاس لهاذو 🤣 فري مدرناش يا مطوري @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/المطور'))
async def dev_info(event):
    if DEV_VIDEO_DATA and await send_dev_video(event.chat_id): return
    await event.reply(f"Dev @{DEVELOPER_USERNAME}\n👑ℙ𝕚𝕡𝕠 ¹⁹\n📍 Sétif")

@client.on(events.NewMessage(pattern='/ايدي'))
async def get_chat_id(event): await event.reply(f"Chat ID: `{event.chat_id}`")

@client.on(events.NewMessage(pattern='/حالة_الحماية'))
async def protection_status(event):
    await event.reply(f"🛡️ الروابط: {'✅' if link_protection else '❌'} | التوجيه: {'✅' if forward_protection else '❌'} | السب: ✅ | القفل: {'🔒' if chat_locked else '🔓'}")

@client.on(events.NewMessage(pattern=r'/مدة_الكتم (\d+)'))
async def set_mute_dur(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='/مدة_الكتم'))
async def show_mute_dur(event): await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='/فك_كل_الكمات'))
async def unmute_all(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    count = 0
    for u in list(mute_status.keys()):
        try: await unmute_user(mute_status[u].get('chat', GROUP_ID), u); del mute_status[u]; count += 1
        except: pass
    await event.reply(f"✅ فك {count} كتم")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_الروابط'))
async def en_link(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = True; await event.reply("✅")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_الروابط'))
async def dis_link(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = False; await event.reply("❌")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_التوجيه'))
async def en_fwd(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = True; await event.reply("✅")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_التوجيه'))
async def dis_fwd(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = False; await event.reply("❌")

@client.on(events.NewMessage(pattern='/فيديو_المطور'))
async def set_dev_vid(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'dev_video'
    await event.reply("📹 ارسل الفيديو في الخاص!")

@client.on(events.NewMessage(pattern='/فيديو_ترحيب'))
async def set_wel_vid(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'welcome'
    await event.reply("ارسل الفيديو او الصورة في الخاص!")

@client.on(events.NewMessage(pattern='/احذف_كامل_الرسائل'))
async def del_all(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if not event.is_private: return
    deleted = 0
    for chat_id in [GROUP_ID] + PROTECTED_CHANNELS:
        try:
            async for msg in client.iter_messages(chat_id, from_user='me', limit=None):
                try: await msg.delete(); deleted += 1
                except: pass
        except: pass
    await event.reply(f"✅ حذف {deleted} رسالة")

@client.on(events.NewMessage(pattern='/زيادة_المدة'))
async def increase_mute(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    data = last_muted_user.get(event.chat_id)
    if not data: return
    buttons = [
        [Button.inline("+10 د", f"add_{data['uid']}_10")],
        [Button.inline("+30 د", f"add_{data['uid']}_30")],
        [Button.inline("+1 س", f"add_{data['uid']}_60")],
    ]
    await event.reply(f"⏰ زيادة كتم {data['name']}:", buttons=buttons)

@client.on(events.CallbackQuery)
async def all_buttons(event):
    data = event.data.decode('utf-8')
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if data.startswith("add_"):
        _, uid, mins = data.split("_"); uid = int(uid); mins = int(mins)
        await mute_user(GROUP_ID, uid, mins * 60)
        name = last_muted_user.get(GROUP_ID, {}).get('name', 'مجهول')
        mute_status[uid] = {'until': time.time() + mins * 60, 'name': name}
        await event.edit(f"✅ +{mins} دقائق لـ {name}"); return
    if data == "mute_dur": await event.reply(f"⏰ {mute_duration // 60} دقائق")
    elif data == "bot_stat":
        muted = len([u for u in mute_status if mute_status[u]['until'] > time.time()])
        await event.reply(f"📊 مكتوم: {muted}")
    elif data == "get_id": await event.reply(f"🆔 {event.chat_id}")
    elif data == "dedikas_cmd": await event.reply(f"ديديكاس 🤣")
    elif data == "unmute_all_btn":
        c = 0
        for u in list(mute_status.keys()):
            try: await unmute_user(mute_status[u].get('chat', GROUP_ID), u); del mute_status[u]; c += 1
            except: pass
        await event.reply(f"🔓 فك {c} كتم")

# ======== حماية المجموعة ========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def group_handler(event):
    global link_protection, forward_protection, chat_locked, mute_duration
    if not event.raw_text: return
    if event.out: return
    sender = await event.get_sender()
    if not sender: return
    if sender.id == BOT_ID: return
    if sender.username == DEVELOPER_USERNAME or sender.id in VIP_USERS: return
    
    text = event.raw_text.strip()
    uid = sender.id; name = sender.first_name or "مجهول"
    
    if link_protection and contains_link(text): await event.delete(); return
    if forward_protection and is_forward(event.message): await event.delete(); return
    
    if contains_swear(text.lower()):
        now = time.time()
        if uid in mute_status and mute_status[uid]['until'] > now: return
        violation_count[uid] += 1
        await event.delete()
        await mute_user(GROUP_ID, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'name': name}
        last_muted_user[GROUP_ID] = {'uid': uid, 'name': name, 'username': sender.username}
        await event.respond(get_mute_message(name, sender.username, mute_duration // 60))
        try:
            await client.send_message(uid, f"⚠️ تحذير\nتم كتمك {mute_duration // 60} دقائق بسبب كلمات ممنوعة.\n👑 @{DEVELOPER_USERNAME}")
        except: pass
        return

@client.on(events.NewMessage(func=lambda e: e.is_private and e.media))
async def handle_media(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return
    media = event.media; mode = dev_media_mode.get(sender.id, 'welcome')
    if mode == 'dev_video':
        if hasattr(media, 'document') and 'video' in media.document.mime_type.lower():
            if await save_dev_video(media): await event.reply("✅ تم الحفظ!")
        if sender.id in dev_media_mode: del dev_media_mode[sender.id]; return
    mt = None
    if hasattr(media, 'photo') and media.photo: mt = 'photo'
    elif hasattr(media, 'document') and 'video' in media.document.mime_type.lower(): mt = 'video'
    if mt and await save_welcome_media(media, mt): await event.reply(f"✅ تم حفظ {mt}!")
    if sender.id in dev_media_mode: del dev_media_mode[sender.id]

@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_pv(event): pass

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

async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        now = datetime.datetime.now(); h, m = now.hour, now.minute
        if h == 22 and m == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            try: await client.send_message(GROUP_ID, f"⚠️ باقي 30 دقيقة على القفل\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        if h == 23 and m == 0 and not chat_locked:
            chat_locked = True; reminder_sent = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=False)
                await client.send_message(GROUP_ID, f"""
╔══════════════════════════════╗
║     🔒 تـم إغـلاق الـمـجـمـوعـة 🔒     ║
╠══════════════════════════════╣
║  ⏰ 12:00 لـيـلاً              ║
║  🚫 تـم قـفـل الـدردشـة        ║
║  ⏳ الـفـتـح: 10:00 صـبـاحـاً    ║
╠══════════════════════════════╣
║     🤖 PIPO BOT 👑 @{DEVELOPER_USERNAME} ║
╚══════════════════════════════╝""")
            except: pass
        if h == 9 and m == 0 and chat_locked:
            chat_locked = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=True)
                await client.send_message(GROUP_ID, f"""
╔══════════════════════════════╗
║     🔓 تـم فـتـح الـمـجـمـوعـة 🔓     ║
╠══════════════════════════════╣
║  ⏰ 10:00 صـبـاحـاً            ║
║  ✅ تـم فـتـح الـدردشـة        ║
║  💬 يمـكـنـكـم الإرسـال الآن     ║
╠══════════════════════════════╣
║     🤖 PIPO BOT 👑 @{DEVELOPER_USERNAME} ║
╚══════════════════════════════╝""")
            except: pass
        await asyncio.sleep(30)

async def auto_unmute():
    while True:
        now = time.time()
        for uid in list(mute_status.keys()):
            if mute_status[uid]['until'] < now:
                try: await unmute_user(GROUP_ID, uid); del mute_status[uid]
                except: pass
        await asyncio.sleep(30)

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
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    await client.run_until_disconnected()

if __name__ == '__main__':
    import fcntl
    lockfile = os.path.join(tempfile.gettempdir(), 'pipo_bot.lock')
    try:
        lock = open(lockfile, 'w')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("❌ نسخة أخرى شغالة!")
        sys.exit(0)
    asyncio.run(main())
