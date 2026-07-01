import asyncio, os, time, random, datetime, re, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest, JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument

API_ID = 33938821
API_HASH = '24a5e855b4cf3ce48e054c32ea725aa4'
BOT_TOKEN = '8957362371:AAGC_GviR84bM0kl3Zmp4Ek9Okq56C9tWJM'
DEVELOPER_USERNAME = 'amirx_xpipo'
DEVELOPER_ID = 8050958688

GROUPS_FILE = "groups.json"
ADMINS_FILE = "admins.json"
WARNINGS_FILE = "warnings.json"
RULES_FILE = "rules.txt"
WELCOME_FILE = "welcome.json"
DEFAULT_ADMINS = [6941580330]

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f: return json.load(f)
    except: pass
    return default

def save_json(path, data):
    with open(path, 'w') as f: json.dump(data, f)

active_groups = set(load_json(GROUPS_FILE, []))
def save_groups(): save_json(GROUPS_FILE, list(active_groups))

admins = load_json(ADMINS_FILE, DEFAULT_ADMINS)
def is_admin(sender): return sender.username == DEVELOPER_USERNAME or sender.id in admins

warnings_data = defaultdict(list, load_json(WARNINGS_FILE, {}))
def save_warnings(): save_json(WARNINGS_FILE, warnings_data)

welcome_media = load_json(WELCOME_FILE, {})
def save_welcome_media(): save_json(WELCOME_FILE, welcome_media)

mute_status = {}
message_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False
reminder_sent = False
last_muted_user = {}
client = TelegramClient('bot', API_ID, API_HASH)
BOT_PHOTO = None

# ---------- مراقبة الخصام والصلح التلقائي ----------
CONFLICT_WORDS = [
    r'\b(يا غبي|يا حمار|يا أحمق|اسكت|اخرس|انقلع|غبي|حمار|غبية|حمقاء|كلب|يا كلب|حيوان)\b',
    r'\b(stupid|shut up|idiot|fool|dumb|moron)\b',
]

conflict_tracker = defaultdict(lambda: defaultdict(list))
CONFLICT_THRESHOLD = 3
CONFLICT_WINDOW = 300
CONFLICT_COOLDOWN = 600

def detect_conflict(text):
    for p in CONFLICT_WORDS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False

# ---------- زخرفة الخطوط ----------
def zakhrif_fraktur(text):
    fraktur_map = {
        'A':'𝕬','B':'𝕭','C':'𝕮','D':'𝕯','E':'𝕰','F':'𝕱','G':'𝕲','H':'𝕳','I':'𝕴','J':'𝕵',
        'K':'𝕶','L':'𝕷','M':'𝕸','N':'𝕹','O':'𝕺','P':'𝕻','Q':'𝕼','R':'𝕽','S':'𝕾','T':'𝕿',
        'U':'𝖀','V':'𝖁','W':'𝖂','X':'𝖃','Y':'𝖄','Z':'𝖅',
        'a':'𝖆','b':'𝖇','c':'𝖈','d':'𝖉','e':'𝖊','f':'𝖋','g':'𝖌','h':'𝖍','i':'𝖎','j':'𝖏',
        'k':'𝖐','l':'𝖑','m':'𝖒','n':'𝖓','o':'𝖔','p':'𝖕','q':'𝖖','r':'𝖗','s':'𝖘','t':'𝖙',
        'u':'𝖚','v':'𝖛','w':'𝖜','x':'𝖝','y':'𝖞','z':'𝖟',
        '0':'𝟎','1':'𝟏','2':'𝟐','3':'𝟑','4':'𝟒','5':'𝟓','6':'𝟔','7':'𝟕','8':'𝟖','9':'𝟗'
    }
    return ''.join(fraktur_map.get(ch, ch) for ch in text)

def zakhrif_script(text):
    script_map = {
        'A':'𝓐','B':'𝓑','C':'𝓒','D':'𝓓','E':'𝓔','F':'𝓕','G':'𝓖','H':'𝓗','I':'𝓘','J':'𝓙',
        'K':'𝓚','L':'𝓛','M':'𝓜','N':'𝓝','O':'𝓞','P':'𝓟','Q':'𝓠','R':'𝓡','S':'𝓢','T':'𝓣',
        'U':'𝓤','V':'𝓥','W':'𝓦','X':'𝓧','Y':'𝓨','Z':'𝓩',
        'a':'𝓪','b':'𝓫','c':'𝓬','d':'𝓭','e':'𝓮','f':'𝓯','g':'𝓰','h':'𝓱','i':'𝓲','j':'𝓳',
        'k':'𝓴','l':'𝓵','m':'𝓶','n':'𝓷','o':'𝓸','p':'𝓹','q':'𝓺','r':'𝓻','s':'𝓼','t':'𝓽',
        'u':'𝓾','v':'𝓿','w':'𝔀','x':'𝔁','y':'𝔂','z':'𝔃',
        '0':'𝟬','1':'𝟭','2':'𝟮','3':'𝟯','4':'𝟰','5':'𝟱','6':'𝟲','7':'𝟳','8':'𝟴','9':'𝟵'
    }
    return ''.join(script_map.get(ch, ch) for ch in text)

async def reply_with_pic(event, text, emoji="", buttons=None):
    decorated = zakhrif_script(text)
    full = f"{emoji} {decorated} {emoji}" if emoji else decorated
    if BOT_PHOTO:
        try: await client.send_file(event.chat_id, BOT_PHOTO, caption=full, buttons=buttons); return
        except: pass
    await event.reply(full, buttons=buttons)

# ---------- كشف السب المتطور ----------
BAD_WORDS = [
    r'\b(كس|طيز|زب|نيك|شرموطة|قحبة|منيكة|منيوك|مسطي|مصطي|قلب|قلبوز)\b',
    r'\b(zeb|zebi|zebbi|kahba|9ahba|9ahb|9hba|kess|kessou|tiz|tizi|3ass|3asska)\b',
    r'\b(قود|god|goud|gawd|gwd)\b',
    r'\b(طحان|طيحان|tahhan|tihan|t7an|t7an|t7han|t7han)\b',
    r'\b(9ahb|9hba|9ahba|9hab|9haba|9hba|9hb|9ahb)\b',
    r'\b(zebi|zebbi|zeb|zbi|zbbi|zebby|zeby)\b',
    r'\b(kess|kes|ks|kessou|kesou|ksou)\b',
    r'\b(tiz|tizi|tizy|tezi|tezy)\b',
    r'\b(3ass|3as|3asska|3aska|3assk)\b',
    r'\b(nik|nikom|nikk|neek|nekk|nkk|n6|n6k)\b',
    r'\b(9wd|9wad|9awd|gawd|goud|god|9od)\b',
    r'ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪﻛﻚ6]',
    r'[كڪﻛﻚګگ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$]',
    r'[ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'[قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ]',
    r'[nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر]',
    r'\b(زبي|زبيي|كسك|طيزك|قحبتك|قحبتي)\b',
    r'\b(يا[\s]*ود[\s]*الكبدة|يا[\s]*ولد[\s]*القحبة|ولد[\s]*الزانية)\b',
    r'\b(نعل[\s]*الدين|نعل[\s]*الوالدين|نعل[\s]*الرب)\b',
    r'\b(الله[\s]*ينعل|الله[\s]*يلعن|ينعل[\s]*دين|يلعن[\s]*دين)\b',
    r'ن\s*م\s*ي',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[مm][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
    r'[ننـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*m[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*e[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ]',
]

LINK_PATTERNS = [r'https?://\S+', r't\.me/\S+', r'www\.\S+']
def contains_swear(t): return any(re.search(p, t, re.I) for p in BAD_WORDS) if t else False
def contains_link(t): return any(re.search(p, t, re.I) for p in LINK_PATTERNS) if t else False
def is_forward(m): return bool(m.forward)

async def mute_user(chat, user, dur):
    try: await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=datetime.datetime.fromtimestamp(time.time()+dur), send_messages=True))); return True
    except: return False
async def unmute_user(chat, user):
    try: await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, send_messages=False))); return True
    except: return False
async def ban_user(chat, user):
    try: await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, view_messages=True))); return True
    except: return False
async def unban_user(chat, user):
    try: await client(EditBannedRequest(chat, user, ChatBannedRights(until_date=None, view_messages=False))); return True
    except: return False

# ---------- الدخول التلقائي ----------
@client.on(events.NewMessage(from_users=DEVELOPER_ID, pattern=r'^/دخول\s+(.+)', func=lambda e: e.is_private))
async def join_group(event):
    arg = event.pattern_match.group(1).strip()
    try:
        if arg.startswith('https://t.me/') or arg.startswith('t.me/'):
            if 'joinchat' in arg or '+' in arg:
                hash_part = arg.split('/')[-1].split('?')[0]
                await client(ImportChatInviteRequest(hash_part))
                return await reply_with_pic(event, "تم الدخول. استخدم /تفعيل داخل المجموعة.")
            else:
                username = arg.rstrip('/').split('/')[-1]
                entity = await client.get_entity(f'@{username}')
        elif arg.startswith('@'):
            entity = await client.get_entity(arg)
        else:
            entity = await client.get_entity(int(arg))
        await client(JoinChannelRequest(entity))
        active_groups.add(entity.id); save_groups()
        await reply_with_pic(event, f"✅ تم دخول المجموعة وتفعيل البوت.\nالآيدي: {entity.id}")
    except Exception as e:
        await reply_with_pic(event, f"❌ فشل الدخول: {str(e)}")

# ---------- الأوامر الإدارية (مع أنماط دقيقة) ----------
@client.on(events.NewMessage(pattern='^/start$'))
async def start(event):
    s = await event.get_sender()
    if s.username == DEVELOPER_USERNAME:
        await reply_with_pic(event, "⚡ PIPO BOT ⚡ 👑 @amirx_xpipo", "🌟", buttons=[
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]
        ])
    else:
        await reply_with_pic(event, "أهلاً، أنا بوت الحماية. استخدم /الاوامر لرؤية كل الأوامر.", "💋")

@client.on(events.NewMessage(pattern='^/تفعيل$'))
async def activate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.add(event.chat_id); save_groups()
    await reply_with_pic(event, "✅ تم تفعيل البوت في هذه المجموعة", "⚡")

@client.on(events.NewMessage(pattern='^/تعطيل$'))
async def deactivate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.discard(event.chat_id); save_groups()
    await reply_with_pic(event, "❌ تم تعطيل البوت في هذه المجموعة")

@client.on(events.NewMessage(pattern='^/المجموعات$'))
async def list_groups(event):
    if not is_admin(await event.get_sender()): return
    if not active_groups: return await reply_with_pic(event, "لا توجد مجموعات مفعلة.")
    txt = "📋 **المجموعات المفعلة:**\n"
    for gid in active_groups:
        try: txt += f"• {(await client.get_entity(gid)).title} ({gid})\n"
        except: txt += f"• {gid}\n"
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/قفل_المجموعة$'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = True
    await client.edit_permissions(event.chat_id, send_messages=False)
    await reply_with_pic(event, "🔒 تم قفل المجموعة", "🔐")

@client.on(events.NewMessage(pattern='^/فك_القفل$'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = False
    await client.edit_permissions(event.chat_id, send_messages=True)
    await reply_with_pic(event, "🔓 تم فتح المجموعة", "🔓")

@client.on(events.NewMessage(pattern='^/ايدي$'))
async def get_id(event): await reply_with_pic(event, f"`{event.chat_id}`")

@client.on(events.NewMessage(pattern='^/حالة_الحماية$'))
async def prot_stat(event):
    await reply_with_pic(event, f"🛡️ الروابط: {'✅' if link_protection else '❌'} | التوجيه: {'✅' if forward_protection else '❌'} | السب: ✅ | القفل: {'🔒' if chat_locked else '🔓'}", "📊")

@client.on(events.NewMessage(pattern=r'^/مدة_الكتم (\d+)$'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await reply_with_pic(event, f"⏰ {mute_duration // 60} دقائق", "⏳")

@client.on(events.NewMessage(pattern='^/مدة_الكتم$'))
async def sh_md(event): await reply_with_pic(event, f"⏰ {mute_duration // 60} دقائق", "⏳")

@client.on(events.NewMessage(pattern='^/فك_كل_الكمات$'))
async def unm_all(event):
    if not is_admin(await event.get_sender()): return
    c = 0
    for u in list(mute_status.keys()):
        try: await unmute_user(event.chat_id, u); del mute_status[u]; c += 1
        except: pass
    await reply_with_pic(event, f"✅ فك {c} كتم", "🔊")

@client.on(events.NewMessage(pattern='^/تفعيل_حماية_الروابط$'))
async def en_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = True
    await reply_with_pic(event, "✅ تم تفعيل حماية الروابط", "🛡️")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_الروابط$'))
async def dis_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = False
    await reply_with_pic(event, "❌ تم تعطيل حماية الروابط", "⚠️")

@client.on(events.NewMessage(pattern='^/تفعيل_حماية_التوجيه$'))
async def en_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = True
    await reply_with_pic(event, "✅ تم تفعيل حماية التوجيه", "🛡️")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_التوجيه$'))
async def dis_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = False
    await reply_with_pic(event, "❌ تم تعطيل حماية التوجيه", "⚠️")

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def perm_mute(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await reply_with_pic(event, "❌ العضو غير موجود")
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time()+ten_years, 'name': target.first_name}
    await reply_with_pic(event, f"🚫 هاك الكتمة يا {target.first_name} 😂", "🚫")

@client.on(events.NewMessage(pattern='^/(حظر|حضر)$', func=lambda e: e.is_reply))
async def ban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await reply_with_pic(event, "❌ العضو غير موجود")
    if target.username == DEVELOPER_USERNAME or target.id in admins: return await reply_with_pic(event, "❌ لا يمكن حظر مسؤول")
    if await ban_user(event.chat_id, target.id): await reply_with_pic(event, f"🚫 {target.first_name} تم حظره", "🚫")
    else: await reply_with_pic(event, "❌ فشل الحظر")

@client.on(events.NewMessage(pattern='^/فك_الحظر$', func=lambda e: e.is_reply))
async def unban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await reply_with_pic(event, "❌ العضو غير موجود")
    if await unban_user(event.chat_id, target.id): await reply_with_pic(event, f"🔓 {target.first_name} تم فك حظره")
    else: await reply_with_pic(event, "❌ فشل فك الحظر")

@client.on(events.NewMessage(pattern='^/تحذير$'))
async def warn(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await reply_with_pic(event, "❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    uid = target.id; name = target.first_name or "لا اسم"
    warnings_data[uid].append(time.time()); save_warnings()
    cur = len(warnings_data[uid])
    await reply_with_pic(event, f"⚠️ {name} تحذير {cur}/3", "⚠️")
    if cur >= 3:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': time.time()+mute_duration, 'name': name}
            await reply_with_pic(event, f"🚫 {name} كتم {mute_duration//60} د", "🚫")
            del warnings_data[uid]; save_warnings()

@client.on(events.NewMessage(pattern='^/عرض_التحذيرات$'))
async def show_warn(event):
    target_id = None; target_name = ""
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id; target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await reply_with_pic(event, "❌ استخدم الأمر مع معرف أو رد")
    c = len(warnings_data.get(target_id, []))
    await reply_with_pic(event, f"📊 {target_name or target_id} لديه {c}/3 تحذيرات", "📋")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = min(int(event.pattern_match.group(1)), 100)
    if count <= 0: return
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    await client.delete_messages(event.chat_id, ids)
    confirm = await reply_with_pic(event, f"🧹 مسح {len(ids)} رسالة")
    await asyncio.sleep(2); await confirm.delete()

@client.on(events.NewMessage(pattern='^/عرض_المكتومين$'))
async def muted_list(event):
    if not mute_status: return await reply_with_pic(event, "✅ لا يوجد مكتومين")
    now = time.time(); txt = "📋 المكتومين:\n"
    for uid, d in mute_status.items():
        rem = int(d['until'] - now)
        if rem > 0:
            try: name = (await client.get_entity(uid)).first_name
            except: name = str(uid)
            txt += f"• {name} - ⏳ {rem//60} د\n"
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/تثبيت$'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await reply_with_pic(event, "❌ رد على رسالة")
    replied = await event.get_reply_message()
    try: await client.pin_message(event.chat_id, replied.id); await reply_with_pic(event, "📌 تم التثبيت", "📌")
    except Exception as e: await reply_with_pic(event, f"❌ فشل: {e}")

@client.on(events.NewMessage(pattern='^/رفع_مسؤول$'))
async def promote_admin(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    target_id = None; target_name = ""
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id; target_name = u.first_name
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await reply_with_pic(event, "❌ أرسل الأمر مع معرف العضو")
    if target_id in admins: return await reply_with_pic(event, "⚠️ مسؤول بالفعل")
    admins.append(target_id); save_json(ADMINS_FILE, admins)
    await reply_with_pic(event, f"✅ تم رفع {target_name or target_id} مسؤولاً", "👑")

@client.on(events.NewMessage(pattern='^/تنزيل_مسؤول$'))
async def demote_admin(event):
    if (await event.get_sender()).username != DEVELOPER_USERNAME: return
    target_id = None
    if event.is_reply:
        u = await (await event.get_reply_message()).get_sender()
        if u: target_id = u.id
    else:
        args = event.raw_text.split()
        if len(args) >= 2:
            try: target_id = int(args[1])
            except: pass
    if not target_id: return await reply_with_pic(event, "❌ أرسل الأمر مع معرف العضو")
    if target_id not in admins: return await reply_with_pic(event, "⚠️ ليس مسؤولاً")
    admins.remove(target_id); save_json(ADMINS_FILE, admins)
    await reply_with_pic(event, "✅ تم تنزيله من المسؤولين", "👋")

# ---------- أوامر الأعضاء ----------
@client.on(events.NewMessage(pattern='/تقرير', func=lambda e: e.is_reply))
async def report(event):
    target_msg = await event.get_reply_message()
    reported_user = await target_msg.get_sender()
    reporter = await event.get_sender()
    if not reported_user or not reporter: return
    report_text = f"📢 **تقرير جديد**\n👤 المُبلّغ: {reporter.first_name}\n🚫 المخالف: {reported_user.first_name}\n💬 الرسالة: {target_msg.raw_text[:200]}"
    for admin_id in admins:
        try: await client.send_message(admin_id, report_text)
        except: pass
    await reply_with_pic(event, "✅ تم إرسال التقرير للمسؤولين")

@client.on(events.NewMessage(pattern='^/قوانين$'))
async def rules(event):
    if not os.path.exists(RULES_FILE): return await reply_with_pic(event, "❌ لم يقم المطور بتعيين القوانين بعد")
    with open(RULES_FILE, 'r') as f: rules_text = f.read()
    await reply_with_pic(event, f"📜 **قوانين المجموعة:**\n{rules_text}")

@client.on(events.NewMessage(pattern='^/معلومات$', func=lambda e: e.is_reply))
async def info(event):
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await reply_with_pic(event, "❌ خطأ")
    uid = target.id
    warns = len(warnings_data.get(uid, []))
    is_muted = "✅ غير مكتوم"
    if uid in mute_status:
        rem = mute_status[uid]['until'] - time.time()
        if rem > 0: is_muted = f"🚫 مكتوم ({int(rem//60)} د)"
    rank = "👤 عضو"
    if target.username == DEVELOPER_USERNAME: rank = "👑 مطور"
    elif uid in admins: rank = "🛡️ مسؤول"
    info_text = f"📋 {target.first_name}\n🆔 {uid}\n⚠️ تحذيرات: {warns}/3\n🔇 {is_muted}\n⭐ {rank}"
    await reply_with_pic(event, info_text)

@client.on(events.NewMessage(pattern='^/توب_المتفاعلين$'))
async def top(event):
    if not message_count: return await reply_with_pic(event, "❌ لا توجد إحصائيات بعد")
    items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
    txt = "🏆 **توب المتفاعلين:**\n"
    for i, (uid, cnt) in enumerate(items, 1):
        try: name = (await client.get_entity(uid)).first_name
        except: name = str(uid)
        txt += f"{i}. {name} - {cnt} رسالة\n"
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/حب$'))
async def love(event):
    args = event.raw_text.split()
    if event.is_reply:
        target = await (await event.get_reply_message()).get_sender()
        u1 = (await event.get_sender()).first_name
        u2 = target.first_name if target else "???"
    elif len(args) >= 3: u1, u2 = args[1], args[2]
    else: return await reply_with_pic(event, "❌ استخدم: /حب @username أو بالرد")
    await reply_with_pic(event, f"{u1} + {u2} = {random.choice(['💔','💖','💘','💕','💓'])} {random.randint(50,100)}%")

@client.on(events.NewMessage(pattern='^/سر$'))
async def secret(event):
    text = event.raw_text[5:].strip()
    if not text: return await reply_with_pic(event, "❌ اكتب رسالة بعد الأمر")
    await event.delete()
    await asyncio.sleep(1)
    await client.send_message(event.chat_id, f"📩 رسالة مجهولة: {text}")

# ---------- معاينة الترحيب ----------
@client.on(events.NewMessage(pattern='^/معاينة_ترحيب$'))
async def preview_welcome(event):
    if not is_admin(await event.get_sender()): return
    if event.chat_id not in active_groups: return await reply_with_pic(event, "❌ البوت غير مفعل هنا.")
    me = await client.get_me()
    name = me.first_name or "المطور"
    uid = me.id
    username = f"@{me.username}" if me.username else "لا يوجد"
    now = datetime.datetime.now()
    date_str = now.strftime('%Y/%m/%d')
    time_str = now.strftime('%I:%M %p')
    group_title = "اسم المجموعة"
    try: group_title = (await client.get_entity(event.chat_id)).title
    except: pass

    try:
        await client.send_message(event.chat_id, "🎉")
        await asyncio.sleep(0.5)
    except: pass

    welcome_text = (
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
        f"⁣⁣ᯓ˹ {zakhrif_fraktur('BIENVENUE DANS LE GROUPE')} ˼\n"
        f"°•——————  『 {zakhrif_fraktur(group_title)} 』 ——————•°\n"
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
        f"°︙ نورت قروبنا يـ  『{zakhrif_fraktur(name)}』 🥂✨\n"
        f"°︙ اسمك ⇚『{zakhrif_fraktur(name)}』\n"
        f"°︙ ايديك ⇚『{uid}』\n"
        f"°︙ يوزرك ⇚『{username}』\n"
        f"°︙ تاريخ انضمامك ☜ {date_str}\n"
        f"°︙ الساعة ☜ {time_str}\n"
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨"
    )

    buttons = [
        [Button.inline("🎉 ترحيب خاص", f"welcomesp_{uid}")],
        [Button.inline("📜 القوانين", "rules_btn"), Button.inline("👤 معلوماتي", f"myinfo_{uid}")],
        [Button.inline("🏆 توب المتفاعلين", "top_btn")]
    ]

    if welcome_media.get('type'):
        try:
            fr_bytes = bytes.fromhex(welcome_media.get('file_reference', '')) if welcome_media.get('file_reference') else b''
            if welcome_media['type'] == 'photo':
                media = InputPhoto(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
            else:
                media = InputDocument(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
            await client.send_file(event.chat_id, media, caption=welcome_text, buttons=buttons)
            return
        except: pass

    await client.send_message(event.chat_id, welcome_text, buttons=buttons)

# ---------- تعيين وسائط الترحيب ----------
@client.on(events.NewMessage(pattern='/تعيين_ترحيب', func=lambda e: e.is_private))
async def set_welcome_media(event):
    sender = await event.get_sender()
    if sender.username != DEVELOPER_USERNAME: return await event.reply("❌ للمطور فقط.")
    if not event.media: return await event.reply("❌ أرسل صورة أو فيديو مع الأمر.")
    media = event.message.media
    try:
        if hasattr(media, 'photo') and media.photo:
            mid = media.photo.id; ah = media.photo.access_hash; fr = media.photo.file_reference or b''
            typ = 'photo'
        elif hasattr(media, 'document') and 'video' in media.document.mime_type.lower():
            mid = media.document.id; ah = media.document.access_hash; fr = media.document.file_reference or b''
            typ = 'video'
        else:
            return await event.reply("❌ يجب أن تكون صورة أو فيديو.")
        welcome_media['type'] = typ
        welcome_media['media_id'] = str(mid)
        welcome_media['access_hash'] = str(ah)
        welcome_media['file_reference'] = fr.hex()
        save_welcome_media()
        await event.reply(f"✅ تم حفظ وسائط الترحيب ({typ}).")
    except Exception as e:
        await event.reply(f"❌ خطأ: {str(e)}")

# ---------- الأوامر العامة ----------
@client.on(events.NewMessage(pattern='/الاوامر|/الأوامر|/اوامر'))
async def all_commands(event):
    txt = (
        "⚡ **جميع أوامر PIPO BOT**\n\n"
        "**🛡️ المسؤول:**\n"
        "/تفعيل - /تعطيل - /قفل_المجموعة - /فك_القفل\n"
        "/كتم (بالرد) - /حظر (بالرد) - /فك_الحظر (بالرد)\n"
        "/تحذير - /عرض_التحذيرات - /مسح عدد\n"
        "/تثبيت - /فك_كل_الكمات - /عرض_المكتومين\n"
        "/مدة_الكتم - /حالة_الحماية - /زيادة_المدة\n"
        "/تفعيل/تعطيل حماية الروابط والتوجيه\n\n"
        "**👤 الأعضاء:**\n"
        "/start - /ايدي - /حب - /سر\n"
        "/توب_المتفاعلين - /قوانين - /معلومات (بالرد)\n"
        "/تقرير (بالرد) - /الاوامر - /مساعدة\n\n"
        "**👑 المطور:**\n"
        "/دخول معرف_المجموعة - /رفع_مسؤول - /تنزيل_مسؤول\n"
        "/المجموعات - /تعيين_ترحيب - /معاينة_ترحيب"
    )
    await reply_with_pic(event, txt)

@client.on(events.NewMessage(pattern='^/مساعدة$'))
async def help_cmd(event):
    await reply_with_pic(event, "📜 اختر فئة الأوامر:", buttons=[
        [Button.inline("🛡️ المسؤول", b"help_admin")],
        [Button.inline("👤 الأعضاء", b"help_member")],
    ])

# ---------- الترحيب الأسطوري ----------
@client.on(events.ChatAction(func=lambda e: e.user_joined))
async def legendary_welcome(event):
    chat = event.chat_id
    if chat not in active_groups: return
    user = await event.get_user()
    if user.bot: return
    await asyncio.sleep(1)

    name = user.first_name or "لاعب"
    uid = user.id
    username = f"@{user.username}" if user.username else "لا يوجد"
    now = datetime.datetime.now()
    date_str = now.strftime('%Y/%m/%d')
    time_str = now.strftime('%I:%M %p')
    group_title = "اسم المجموعة"
    try: group_title = (await client.get_entity(chat)).title
    except: pass

    try:
        await client.send_message(chat, "🎉")
        await asyncio.sleep(0.5)
    except: pass

    welcome_text = (
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
        f"⁣⁣ᯓ˹ {zakhrif_fraktur('BIENVENUE DANS LE GROUPE')} ˼\n"
        f"°•——————  『 {zakhrif_fraktur(group_title)} 』 ——————•°\n"
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨\n"
        f"°︙ نورت قروبنا يـ  『{zakhrif_fraktur(name)}』 🥂✨\n"
        f"°︙ اسمك ⇚『{zakhrif_fraktur(name)}』\n"
        f"°︙ ايديك ⇚『{uid}』\n"
        f"°︙ يوزرك ⇚『{username}』\n"
        f"°︙ تاريخ انضمامك ☜ {date_str}\n"
        f"°︙ الساعة ☜ {time_str}\n"
        f"▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨▨"
    )

    buttons = [
        [Button.inline("🎉 ترحيب خاص", f"welcomesp_{uid}")],
        [Button.inline("📜 القوانين", "rules_btn"), Button.inline("👤 معلوماتي", f"myinfo_{uid}")],
        [Button.inline("🏆 توب المتفاعلين", "top_btn")]
    ]

    if welcome_media.get('type'):
        try:
            fr_bytes = bytes.fromhex(welcome_media.get('file_reference', '')) if welcome_media.get('file_reference') else b''
            if welcome_media['type'] == 'photo':
                media = InputPhoto(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
            else:
                media = InputDocument(id=int(welcome_media['media_id']), access_hash=int(welcome_media['access_hash']), file_reference=fr_bytes)
            await client.send_file(chat, media, caption=welcome_text, buttons=buttons)
            return
        except: pass

    await client.send_message(chat, welcome_text, buttons=buttons)

# ---------- أزرار الترحيب ----------
@client.on(events.CallbackQuery)
async def welcome_buttons(event):
    data = event.data.decode('utf-8')
    if data.startswith("welcomesp_"):
        _, uid = data.split("_")
        try: await client.send_message(int(uid), "🎉 أهلاً وسهلاً! نتمنى لك أجمل الأوقات. 👋")
        except: pass
    elif data == "rules_btn":
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r') as f: txt = f.read()
            await event.answer(txt[:200], alert=True)
        else: await event.answer("لا توجد قوانين بعد.", alert=True)
    elif data.startswith("myinfo_"):
        uid = int(data.split("_")[1])
        warns = len(warnings_data.get(uid, []))
        is_muted = "غير مكتوم" if uid not in mute_status or mute_status[uid]['until'] < time.time() else "مكتوم"
        info = f"تحذيرات: {warns}/3\nكتم: {is_muted}"
        await event.answer(info, alert=True)
    elif data == "top_btn":
        if not message_count: await event.answer("لا بيانات بعد.", alert=True)
        else:
            items = sorted(message_count.items(), key=lambda x: x[1], reverse=True)[:5]
            txt = "\n".join(f"{i}. {name}" for i, (uid, _) in enumerate(items, 1) if (name := (await client.get_entity(uid)).first_name))
            await event.answer(txt, alert=True)
    else:
        if data == "mute_dur": await event.reply(f"⏰ {mute_duration//60} د")
        elif data == "bot_stat": await event.reply(f"📊 مكتوم: {len(mute_status)}")
        elif data == "get_id": await event.reply(f"🆔 {event.chat_id}")
        elif data == "unmute_all_btn":
            for u in list(mute_status.keys()):
                try: await unmute_user(event.chat_id, u); del mute_status[u]
                except: pass
            await event.reply("🔓 فك الكل")
        elif data.startswith("add_"):
            if not is_admin(await event.get_sender()): return
            _, uid, mins = data.split("_"); uid = int(uid); mins = int(mins)
            await mute_user(event.chat_id, uid, mins*60)
            mute_status[uid] = {'until': time.time()+mins*60}
            await event.edit(f"✅ +{mins} دقائق")
        elif data == "help_admin":
            await event.edit("🛡️ أوامر المسؤول:\n/تفعيل /تعطيل /قفل /فك /كتم /حظر /فك_الحظر /تحذير /مسح /تثبيت /مدة_الكتم /فك_كل /حماية /عرض_المكتومين /مساعدة")
        elif data == "help_member":
            await event.edit("👤 أوامر الأعضاء:\n/start /حب /سر /توب_المتفاعلين /قوانين /معلومات /تقرير /الاوامر /مساعدة")

# ---------- حماية تلقائية مع مراقبة الخصام ----------
@client.on(events.NewMessage())
async def global_handler(event):
    global link_protection, forward_protection, mute_duration
    if not event.is_group or not event.raw_text or event.out: return
    chat = event.chat_id
    if chat not in active_groups: return
    sender = await event.get_sender()
    if not sender or sender.id == (await client.get_me()).id: return
    if sender.username == DEVELOPER_USERNAME: return
    message_count[sender.id] += 1
    text = event.raw_text.strip()

    if link_protection and contains_link(text): await event.delete(); return
    if forward_protection and is_forward(event.message): await event.delete(); return

    if contains_swear(text.lower()):
        now = time.time(); uid = sender.id; name = sender.first_name or "مجهول"
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        if await mute_user(chat, uid, mute_duration):
            mute_status[uid] = {'until': now+mute_duration, 'name': name}
            await client.send_message(chat, f"🚫 {name} كتم {mute_duration//60} د")

    if detect_conflict(text):
        reply = await event.get_reply_message()
        if reply:
            other_user = await reply.get_sender()
            if other_user and other_user.id != sender.id:
                pair = tuple(sorted((sender.id, other_user.id)))
                now_ts = time.time()
                conflict_tracker[pair][sender.id] = [t for t in conflict_tracker[pair][sender.id] if now_ts - t < CONFLICT_WINDOW]
                conflict_tracker[pair][other_user.id] = [t for t in conflict_tracker[pair][other_user.id] if now_ts - t < CONFLICT_WINDOW]
                conflict_tracker[pair][sender.id].append(now_ts)
                total_conflicts = len(conflict_tracker[pair][sender.id]) + len(conflict_tracker[pair][other_user.id])
                if total_conflicts >= CONFLICT_THRESHOLD:
                    last_reconcile = conflict_tracker[pair].get('last_reconcile', 0)
                    if now_ts - last_reconcile > CONFLICT_COOLDOWN:
                        conflict_tracker[pair]['last_reconcile'] = now_ts
                        try:
                            await client.send_message(chat,
                                "🕊️ لقد لاحظت تبادل كلمات حادة بينكما.\n"
                                "أرجو منكما التوقف فوراً، فأنتم إخوة.\n"
                                "قال تعالى: {وَأَصْلِحُوا ذَاتَ بَيْنِكُمْ}.\n"
                                "تصافحوا وتآخوا، فما أجمل الودّ! 🌹"
                            )
                        except: pass

# ---------- القفل والفتح التلقائي بتوقيت الجزائر ----------
async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_dz = now_utc + datetime.timedelta(hours=1)
        h, m = now_dz.hour, now_dz.minute

        if h == 23 and m == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            for gid in active_groups:
                try:
                    await client.send_message(gid,
                        f"⚠️ تنبيه: سيتم قفل المجموعة بعد 30 دقيقة (منتصف الليل بتوقيت الجزائر).\n"
                        f"🔓 ستعاود الفتح الساعة 10:00 صباحاً.\n"
                        f"👑 @{DEVELOPER_USERNAME}"
                    )
                except: pass

        if h == 0 and m == 0 and not chat_locked:
            chat_locked = True
            reminder_sent = False
            for gid in active_groups:
                try:
                    await client.edit_permissions(gid, send_messages=False)
                    await client.send_message(gid,
                        f"🔒 تم قفل المجموعة تلقائياً – منتصف الليل.\n"
                        f"🌙 ستعود للفتح الساعة 10:00 صباحاً بتوقيت الجزائر.\n"
                        f"👑 @{DEVELOPER_USERNAME}"
                    )
                except: pass

        if h == 10 and m == 0 and chat_locked:
            chat_locked = False
            for gid in active_groups:
                try:
                    await client.edit_permissions(gid, send_messages=True)
                    await client.send_message(gid,
                        f"🔓 تم فتح المجموعة تلقائياً – صباح الخير!\n"
                        f"☀️ استمتعوا بيومكم.\n"
                        f"👑 @{DEVELOPER_USERNAME}"
                    )
                except: pass

        await asyncio.sleep(30)

async def auto_unmute():
    while True:
        now = time.time()
        for uid in list(mute_status.keys()):
            if mute_status[uid]['until'] < now:
                for gid in active_groups:
                    try: await unmute_user(gid, uid)
                    except: pass
                del mute_status[uid]
        await asyncio.sleep(30)

async def main():
    global BOT_PHOTO
    await client.start(bot_token=BOT_TOKEN)
    photos = await client.get_profile_photos('me', limit=1)
    if photos:
        BOT_PHOTO = InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)
    print(f"✅ PIPO BOT جاهز في {len(active_groups)} مجموعات")
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
