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
DEVELOPER_ID = 8050958688
VIP_USERS = [6941580330, 8050958688]

PROTECTED_CHANNELS = [CHANNEL_1, CHANNEL_2, CHANNEL_3]

mute_status = {}
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

BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلب|قلبوز)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'(ن\s*ي\s*ك|ن\s*ي\s*6|ن\s*ق\s*ش)',
    r'(ك\s*س|ك\s*ص|ڪ\s*س|ك\s*5)',
    r'(ط\s*ي\s*ز|ط\s*ي\s*ظ)',
    r'(ز\s*ب|ز\s*ب\s*ي|ز\s*پ)',
    r'(ق\s*ح\s*ب|9\s*ح\s*ب|ڨ\s*ح\s*ب)',
    r'\b(زبي|كسك|طيزك|قحبتك)\b',
    r'\b(ك\sس|ك\sص|ط\sي\sز|ز\sب|ن\sي\sك|ق\sح\sب)\b',
]

LINK_PATTERNS = [
    r'https?://\S+', r'http?://\S+', r't\.me/\S+', r'telegram\.me/\S+', r'www\.\S+',
    r'\S+\.com\b', r'\S+\.net\b', r'\S+\.org\b', r'\S+\.io\b', r'\S+\.app\b',
    r'tiktok\.com', r'youtube\.com', r'youtu\.be', r'instagram\.com', r'facebook\.com',
]

THE_ONLY_ROAST = "يا خو شحال تهدر بلع علينا فومك صدعتنا"

def get_mute_message(name, username, duration):
    violator = f"@{username}" if username else name
    return f"""
╔══════════════════════════════╗
║     🚫 تـم كـتـم عـضـو 🚫       ║
╠══════════════════════════════╣
║  👤 الـمـخـالـف: {violator}     ║
║  ⏰ مـدة الـكـتـم: {duration} دقـائـق  ║
║  🤬 الـسـبـب: كـلـمـات مـمـنـوعـة   ║
╠══════════════════════════════╣
║  👑 @{DEVELOPER_USERNAME}     ║
╚══════════════════════════════╝
"""

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

# ======== ⭐ جميع الأوامر - بدون تكرار ⭐ ========
@client.on(events.NewMessage(pattern='/قفل_المجموعة'))
async def lock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked
    chat_locked = True
    await client.edit_permissions(GROUP_ID, send_messages=False)
    await event.reply(f"🔒 **تم قفل المجموعة**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/فك_القفل'))
async def unlock_chat(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global chat_locked
    chat_locked = False
    await client.edit_permissions(GROUP_ID, send_messages=True)
    await event.reply(f"🔓 **تم فتح المجموعة**\n👑 @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/ديرلهم_ديديكاس'))
async def dedikas(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return
    await event.reply(f"ديديكاس لهاذو 🤣 فري مدرناش يا مطوري @{DEVELOPER_USERNAME}")

@client.on(events.NewMessage(pattern='/المطور'))
async def dev_info(event):
    if DEV_VIDEO_DATA and await send_dev_video(event.chat_id): return
    await event.reply(f"""Dev @{DEVELOPER_USERNAME}
👑ℙ𝕚𝕡𝕠 ¹⁹
📍 Sétif""")

@client.on(events.NewMessage(pattern='/فيديو_المطور'))
async def set_dev_video(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    dev_media_mode[(await event.get_sender()).id] = 'dev_video'
    await event.reply("📹 ارسل الفيديو في الخاص!")

@client.on(events.NewMessage(pattern='/ايدي'))
async def get_chat_id(event):
    await event.reply(f"Chat ID: `{event.chat_id}`")

@client.on(events.NewMessage(pattern=r'/مدة_الكتم (\d+)'))
async def set_mute_duration(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق")

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
            await event.reply(f"✅ تم فك الكتم عن {name}")
    except: pass

@client.on(events.NewMessage(pattern='/فك_كل_الكمات'))
async def unmute_all(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    count = 0
    for uid in list(mute_status.keys()):
        try: await unmute_user(mute_status[uid].get('chat', GROUP_ID), uid); del mute_status[uid]; count += 1
        except: pass
    await event.reply(f"✅ تم فك {count} كتم")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_الروابط'))
async def enable_link(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = True
    await event.reply("✅ تم تفعيل حماية الروابط")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_الروابط'))
async def disable_link(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global link_protection; link_protection = False
    await event.reply("❌ تم تعطيل حماية الروابط")

@client.on(events.NewMessage(pattern='/تفعيل_حماية_التوجيه'))
async def enable_fwd(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = True
    await event.reply("✅ تم تفعيل حماية التوجيه")

@client.on(events.NewMessage(pattern='/تعطيل_حماية_التوجيه'))
async def disable_fwd(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    global forward_protection; forward_protection = False
    await event.reply("❌ تم تعطيل حماية التوجيه")

@client.on(events.NewMessage(pattern='/حالة_الحماية'))
async def protection_status(event):
    await event.reply(f"""
🛡️ حالة الحماية:
🔗 الروابط: {'✅' if link_protection else '❌'}
↩️ التوجيه: {'✅' if forward_protection else '❌'}
🤬 السب: ✅
🔒 القفل: {'🔒' if chat_locked else '🔓'}
""")

@client.on(events.NewMessage(pattern='/احذف_كامل_الرسائل'))
async def delete_all_msgs(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if not event.is_private: return
    deleted = 0
    for chat_id in [GROUP_ID] + PROTECTED_CHANNELS:
        try:
            async for msg in client.iter_messages(chat_id, from_user='me', limit=None):
                try: await msg.delete(); deleted += 1
                except: pass
        except: pass
    await event.reply(f"✅ تم حذف {deleted} رسالة")

# ======== ⭐ زيادة مدة الكتم ⭐ ========
@client.on(events.NewMessage(pattern='/زيادة_المدة'))
async def increase_mute(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if not event.is_reply: return
    
    if event.chat_id not in last_muted_user: return
    
    data = last_muted_user[event.chat_id]
    uid = data['uid']; name = data['name']
    
    buttons = [
        [Button.inline("+10 دقائق", f"add_{uid}_10")],
        [Button.inline("+30 دقيقة", f"add_{uid}_30")],
        [Button.inline("+1 ساعة", f"add_{uid}_60")],
        [Button.inline("+3 ساعات", f"add_{uid}_180")],
    ]
    
    await event.reply(f"⏰ زيادة كتم {name}\nاختر المدة:", buttons=buttons)

@client.on(events.CallbackQuery)
async def handle_add_mute(event):
    data = event.data.decode('utf-8')
    if not data.startswith("add_"): return
    if (await event.get_sender()).username != DEVELOPER_USERNAME:
        await event.answer("🚫 للمطور فقط!", alert=True)
        return
    
    _, uid, mins = data.split("_")
    uid = int(uid); mins = int(mins)
    
    await mute_user(GROUP_ID, uid, mins * 60)
    name = last_muted_user.get(GROUP_ID, {}).get('name', 'مجهول')
    mute_status[uid] = {'until': time.time() + mins * 60, 'name': name}
    
    await event.edit(f"✅ تمت زيادة كتم {name} +{mins} دقائق")

# ======== start ========
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender = await event.get_sender()
    if sender.username == DEVELOPER_USERNAME:
        msg = f"""⚡ **PIPO BOT** ⚡
👑 **أهلاً مطوري @{DEVELOPER_USERNAME}**
📋 **لوحة التحكم:**"""
        buttons = [
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة البوت", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("😂 ديديكاس", b"dedikas_cmd")],
            [Button.inline("🔓 فك كل الكمات", b"unmute_all_btn")],
        ]
        await send_with_bot_photo(event.chat_id, msg, buttons)
    else:
        try: await event.react("❤️")
        except: pass

@client.on(events.CallbackQuery)
async def main_buttons(event):
    data = event.data.decode('utf-8')
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    if data == "mute_dur": await event.reply(f"⏰ مدة الكتم: {mute_duration // 60} دقائق")
    elif data == "bot_stat":
        muted = len([u for u in mute_status if mute_status[u]['until'] > time.time()])
        await event.reply(f"📊 حالة البوت\n🔇 مكتوم: {muted}")
    elif data == "get_id": await event.reply(f"🆔 {event.chat_id}")
    elif data == "dedikas_cmd": await event.reply(f"ديديكاس لهاذو 🤣")
    elif data == "unmute_all_btn":
        count = 0
        for uid in list(mute_status.keys()):
            try: await unmute_user(mute_status[uid].get('chat', GROUP_ID), uid); del mute_status[uid]; count += 1
            except: pass
        await event.reply(f"🔓 تم فك {count} كتم")

# ======== حماية الروابط والتوجيه ========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def protect_links(event):
    if not event.raw_text or event.out: return
    sender = await event.get_sender()
    if sender and (sender.id == BOT_ID or sender.username == DEVELOPER_USERNAME or sender.id in VIP_USERS): return
    
    if link_protection and contains_link(event.raw_text):
        await event.delete()
        return
    
    if forward_protection and is_forward(event.message):
        await event.delete()
        return

# ======== فلترة السب ========
@client.on(events.NewMessage(chats=[GROUP_ID]))
async def filter_bad(event):
    if not event.raw_text or event.out: return
    sender = await event.get_sender()
    if sender and (sender.id == BOT_ID or sender.username == DEVELOPER_USERNAME or sender.id in VIP_USERS): return
    if not contains_swear(event.raw_text.lower()): return
    
    uid = sender.id; name = sender.first_name or "مجهول"
    now = time.time()
    
    if uid in mute_status and mute_status[uid]['until'] > now: return
    
    await event.delete()
    await mute_user(event.chat_id, uid, mute_duration)
    mute_status[uid] = {'until': now + mute_duration, 'name': name}
    last_muted_user[event.chat_id] = {'uid': uid, 'name': name, 'username': sender.username}
    
    msg = get_mute_message(name, sender.username, mute_duration // 60)
    await event.respond(msg)

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
    await event.reply("ارسل الفيديو او الصورة في الخاص!")

@client.on(events.NewMessage(func=lambda e: e.is_private and e.media))
async def handle_dev_media(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return
    media = event.media; media_type = None
    mode = dev_media_mode.get(sender.id, 'welcome')
    if mode == 'dev_video':
        if hasattr(media, 'document') and 'video' in media.document.mime_type.lower():
            if await save_dev_video(media): await event.reply("✅ تم الحفظ!")
        else: await event.reply("❌ ارسل فيديو!")
        if sender.id in dev_media_mode: del dev_media_mode[sender.id]
        return
    if hasattr(media, 'photo') and media.photo: media_type = 'photo'
    elif hasattr(media, 'document') and 'video' in media.document.mime_type.lower(): media_type = 'video'
    if not media_type: return
    if await save_welcome_media(media, media_type): await event.reply(f"✅ تم حفظ {media_type}!")
    if sender.id in dev_media_mode: del dev_media_mode[sender.id]

# ======== الخاص ========
@client.on(events.NewMessage(func=lambda e: e.is_private))
async def handle_private(event):
    pass

# ======== قفل تلقائي ========
async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        now = datetime.datetime.now()
        hour, minute = now.hour, now.minute
        
        if hour == 22 and minute == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            try: await client.send_message(GROUP_ID, f"⚠️ تنبيه: باقي 30 دقيقة على القفل\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        
        if hour == 23 and minute == 0 and not chat_locked:
            chat_locked = True; reminder_sent = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=False)
                await client.send_message(GROUP_ID, f"🔒 تم إغلاق المحادثة\n⏰ 12:00 ليلاً\n🔓 الفتح: 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}")
            except: pass
        
        if hour == 9 and minute == 0 and chat_locked:
            chat_locked = False
            try:
                await client.edit_permissions(GROUP_ID, send_messages=True)
                await client.send_message(GROUP_ID, f"🔓 تم فتح المحادثة\n⏰ 10:00 صباحاً\n👑 @{DEVELOPER_USERNAME}")
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
    
    # فتح المجموعة عند التشغيل
    global chat_locked
    try:
        await client.edit_permissions(GROUP_ID, send_messages=True)
        chat_locked = False
    except: pass
    
    print(f"✅ PIPO BOT: @{me.username}")
    print(f"👑 @{DEVELOPER_USERNAME}")
    print(f"🔓 فتح عند التشغيل")
    print(f"🌙 قفل: 23:00 UTC")
    print(f"☀️ فتح: 9:00 UTC")
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
