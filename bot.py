import asyncio, os, time, random, datetime, re, json
from collections import defaultdict
from telethon import TelegramClient, events, Button
from telethon.tl.functions.channels import EditBannedRequest, JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import ChatBannedRights, InputPhoto, InputDocument
from aiohttp import web

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
CHANNEL_LIMITS_FILE = "channel_limits.json"
AUTO_SETTINGS_FILE = "auto_settings.json"
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

channel_limits = load_json(CHANNEL_LIMITS_FILE, {})
user_channel_msgs = defaultdict(lambda: defaultdict(list))
user_mute_warnings = defaultdict(lambda: defaultdict(float))

mute_status = {}
message_count = defaultdict(int)
mute_duration = 300
link_protection = True
forward_protection = True
chat_locked = False
reminder_sent = False
client = TelegramClient('bot', API_ID, API_HASH)
BOT_PHOTO = None

bot_settings = load_json(AUTO_SETTINGS_FILE, {"auto_lock_enabled": False})
def save_settings(): save_json(AUTO_SETTINGS_FILE, bot_settings)

# ---------- Health check ----------
async def handle_health(request):
    return web.Response(text="OK")

# ---------- كشف السب ----------
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
    r'ن[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*ي[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[كڪKbB6]',
    r'[كڪKbB][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[سښصث5\$]',
    r'[ططـظظـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[يىېۍ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[زژڗژظڞ]',
    r'[زژڗژ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'[قڨ9][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ححـ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[ببـپپـ]',
    r'f[\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[uوؤ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[cكڪ][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[kكڪ]',
    r'[nن][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[i1!|][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[gج][\s\.\,\;\:\!\@\#\$\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[e3][\s\.\,\;\:\!\@\#\$\%\^\&\*\(\)\-\+\=\[\]\{\}\\\|\/\?\<\>\~]*[rر]',
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

# ---------- API للوحة التحكم ----------
API_TOKEN = "pipomaster2026"

async def handle_api(request):
    token = request.headers.get('X-Bot-Token', '')
    if token != API_TOKEN:
        return web.json_response({'error': 'Unauthorized'}, status=403)
    
    path = request.path
    data = await request.json() if request.method == 'POST' else {}
    
    if path == '/api/stats':
        return web.json_response({
            'totalGroups': len(active_groups),
            'totalMuted': len([u for u in mute_status if mute_status[u]['until'] > time.time()]),
            'totalBanned': 0,
            'totalWarnings': sum(len(v) for v in warnings_data.values())
        })
    
    if path == '/api/groups':
        groups = []
        for gid in active_groups:
            try:
                entity = await client.get_entity(gid)
                groups.append({'id': gid, 'name': entity.title})
            except:
                groups.append({'id': gid, 'name': str(gid)})
        return web.json_response({'groups': groups})
    
    if path == '/api/broadcast':
        msg = data.get('message', '')
        if not msg:
            return web.json_response({'error': 'No message'})
        c = 0
        for gid in active_groups:
            try:
                await client.send_message(gid, f"📢 **رسالة من المطور:**\n\n{msg}\n\n👑 @{DEVELOPER_USERNAME}")
                c += 1
            except: pass
        return web.json_response({'success': True, 'count': c})
    
    if path == '/api/leave':
        gid = data.get('group_id')
        if gid:
            try:
                await client.send_message(gid, f"🚨 BAAY! أنا طالع من المجموعة بأمر من المطور.\n👑 @{DEVELOPER_USERNAME}")
                await client(LeaveChannelRequest(gid))
                active_groups.discard(gid); save_groups()
                return web.json_response({'success': True})
            except: pass
        return web.json_response({'error': 'Failed'})
    
    if path == '/api/globalban':
        uid = data.get('user_id')
        remove = data.get('remove', False)
        if uid:
            if remove:
                for gid in active_groups:
                    try: await unban_user(gid, uid)
                    except: pass
                return web.json_response({'success': True})
            else:
                for gid in active_groups:
                    try: await ban_user(gid, uid)
                    except: pass
                return web.json_response({'success': True})
        return web.json_response({'error': 'No user_id'})
    
    return web.json_response({'error': 'Unknown endpoint'})

# ---------- الأوامر ----------
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    s = await event.get_sender()
    if is_admin(s):
        await event.reply("⚡ PIPO BOT ⚡ 👑 @amirx_xpipo", buttons=[
            [Button.inline("🔇 مدة الكتم", b"mute_dur"), Button.inline("📊 حالة", b"bot_stat")],
            [Button.inline("🆔 الآيدي", b"get_id"), Button.inline("🔓 فك الكل", b"unmute_all_btn")]
        ])
    else:
        await event.reply("أهلاً، أنا بوت الحماية. استخدم /الاوامر لرؤية كل الأوامر. 💋")

@client.on(events.NewMessage(pattern='^/تفعيل$'))
async def activate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.add(event.chat_id); save_groups()
    await event.reply("✅ تم تفعيل البوت في هذه المجموعة")

@client.on(events.NewMessage(pattern='^/تعطيل$'))
async def deactivate_group(event):
    if not is_admin(await event.get_sender()): return
    active_groups.discard(event.chat_id); save_groups()
    await event.reply("❌ تم تعطيل البوت في هذه المجموعة")

@client.on(events.NewMessage(pattern='^/قفل_المجموعة$'))
async def lock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = True
    await client.edit_permissions(event.chat_id, send_messages=False)
    await event.reply("🔒 تم قفل المجموعة")

@client.on(events.NewMessage(pattern='^/فك_القفل$'))
async def unlock_chat(event):
    if not is_admin(await event.get_sender()): return
    global chat_locked; chat_locked = False
    await client.edit_permissions(event.chat_id, send_messages=True)
    await event.reply("🔓 تم فتح المجموعة")

@client.on(events.NewMessage(pattern='^/تفعيل_القفل_التلقائي$'))
async def enable_auto_lock(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["auto_lock_enabled"] = True
    save_settings()
    await event.reply("🕒 **تم تفعيل القفل التلقائي للمجموعة**\nسيتم القفل منتصف الليل والفتح 10 صباحاً بتوقيت الجزائر.")

@client.on(events.NewMessage(pattern='^/تعطيل_القفل_التلقائي$'))
async def disable_auto_lock(event):
    if not is_admin(await event.get_sender()): return
    bot_settings["auto_lock_enabled"] = False
    save_settings()
    await event.reply("❌ **تم تعطيل القفل التلقائي للمجموعة**")

@client.on(events.NewMessage(pattern='^/حالة_الحماية$'))
async def prot_stat(event):
    await event.reply(f"🛡️ الروابط: {'✅' if link_protection else '❌'} | التوجيه: {'✅' if forward_protection else '❌'} | السب: ✅ | القفل التلقائي: {'✅' if bot_settings.get('auto_lock_enabled', False) else '❌'} | القفل اليدوي: {'🔒' if chat_locked else '🔓'}")

@client.on(events.NewMessage(pattern=r'^/مدة_الكتم (\d+)$'))
async def set_md(event):
    if not is_admin(await event.get_sender()): return
    global mute_duration; mute_duration = int(event.pattern_match.group(1)) * 60
    await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='^/مدة_الكتم$'))
async def sh_md(event): await event.reply(f"⏰ {mute_duration // 60} دقائق")

@client.on(events.NewMessage(pattern='^/فك_كل_الكمات$'))
async def unm_all(event):
    if not is_admin(await event.get_sender()): return
    c = 0
    for u in list(mute_status.keys()):
        try: await unmute_user(event.chat_id, u); del mute_status[u]; c += 1
        except: pass
    await event.reply(f"✅ فك {c} كتم")

@client.on(events.NewMessage(pattern='^/تفعيل_حماية_الروابط$'))
async def en_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = True
    await event.reply("✅ تم تفعيل حماية الروابط")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_الروابط$'))
async def dis_l(event):
    if not is_admin(await event.get_sender()): return
    global link_protection; link_protection = False
    await event.reply("❌ تم تعطيل حماية الروابط")

@client.on(events.NewMessage(pattern='^/تفعيل_حماية_التوجيه$'))
async def en_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = True
    await event.reply("✅ تم تفعيل حماية التوجيه")

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_التوجيه$'))
async def dis_f(event):
    if not is_admin(await event.get_sender()): return
    global forward_protection; forward_protection = False
    await event.reply("❌ تم تعطيل حماية التوجيه")

@client.on(events.NewMessage(pattern='/كتم', func=lambda e: e.is_reply))
async def perm_mute(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ العضو غير موجود")
    ten_years = 10*365*24*3600
    await mute_user(event.chat_id, target.id, ten_years)
    mute_status[target.id] = {'until': time.time()+ten_years, 'name': target.first_name}
    await event.reply(f"🚫 هاك الكتمة يا {target.first_name} 😂")

@client.on(events.NewMessage(pattern='^/(حظر|حضر)$', func=lambda e: e.is_reply))
async def ban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ العضو غير موجود")
    if target.username == DEVELOPER_USERNAME or target.id in admins: return await event.reply("❌ لا يمكن حظر مسؤول")
    if await ban_user(event.chat_id, target.id): await event.reply(f"🚫 {target.first_name} تم حظره")
    else: await event.reply("❌ فشل الحظر")

@client.on(events.NewMessage(pattern='^/فك_الحظر$', func=lambda e: e.is_reply))
async def unban_handler(event):
    if not is_admin(await event.get_sender()): return
    target = await (await event.get_reply_message()).get_sender()
    if not target: return await event.reply("❌ العضو غير موجود")
    if await unban_user(event.chat_id, target.id): await event.reply(f"🔓 {target.first_name} تم فك حظره")
    else: await event.reply("❌ فشل فك الحظر")

@client.on(events.NewMessage(pattern='^/تحذير$'))
async def warn(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ يجب الرد على الشخص")
    target = await (await event.get_reply_message()).get_sender()
    if not target: return
    uid = target.id; name = target.first_name or "لا اسم"
    warnings_data[uid].append(time.time()); save_warnings()
    cur = len(warnings_data[uid])
    await event.reply(f"⚠️ {name} تحذير {cur}/3")
    if cur >= 3:
        if await mute_user(event.chat_id, uid, mute_duration):
            mute_status[uid] = {'until': time.time()+mute_duration, 'name': name}
            await event.reply(f"🚫 {name} كتم {mute_duration//60} د")
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
    if not target_id: return await event.reply("❌ استخدم الأمر مع معرف أو رد")
    c = len(warnings_data.get(target_id, []))
    await event.reply(f"📊 {target_name or target_id} لديه {c}/3 تحذيرات")

@client.on(events.NewMessage(pattern=r'^/مسح\s+(\d+)$'))
async def purge(event):
    if not is_admin(await event.get_sender()): return
    count = int(event.pattern_match.group(1))
    if count <= 0: return await event.reply("❌ الرجاء إدخال عدد صحيح موجب.")
    if count > 100: return await event.reply("❌ الحد الأقصى هو 100 رسالة.")
    await event.delete()
    msgs = await client.get_messages(event.chat_id, limit=count)
    ids = [m.id for m in msgs if m]
    if not ids: return
    await client.delete_messages(event.chat_id, ids)
    confirm = await event.respond(f"🧹 تم مسح {len(ids)} رسالة.")
    await asyncio.sleep(2); await confirm.delete()

@client.on(events.NewMessage(pattern='^/تثبيت$'))
async def pin_msg(event):
    if not is_admin(await event.get_sender()): return
    if not event.is_reply: return await event.reply("❌ رد على رسالة")
    replied = await event.get_reply_message()
    try: await client.pin_message(event.chat_id, replied.id); await event.reply("📌 تم التثبيت")
    except Exception as e: await event.reply(f"❌ فشل: {e}")

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
    if not target_id: return await event.reply("❌ أرسل الأمر مع معرف العضو")
    if target_id in admins: return await event.reply("⚠️ مسؤول بالفعل")
    admins.append(target_id); save_json(ADMINS_FILE, admins)
    await event.reply(f"✅ تم رفع {target_name or target_id} مسؤولاً")

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
    if not target_id: return await event.reply("❌ أرسل الأمر مع معرف العضو")
    if target_id not in admins: return await event.reply("⚠️ ليس مسؤولاً")
    admins.remove(target_id); save_json(ADMINS_FILE, admins)
    await event.reply("✅ تم تنزيله من المسؤولين")

# ================= حماية القنوات =================
@client.on(events.NewMessage(pattern='^/تفعيل_حماية_القنوات$'))
async def enable_channel_protection(event):
    if not is_admin(await event.get_sender()): return
    channel_limits[event.chat_id] = {"max_msgs": 3, "window": 300}
    save_json(CHANNEL_LIMITS_FILE, channel_limits)
    await event.reply("🛡️ **تم تفعيل حماية القناة**\n📨 3 رسائل فقط كل 5 دقائق لكل عضو.\n👑 المطور: @" + DEVELOPER_USERNAME)

@client.on(events.NewMessage(pattern='^/تعطيل_حماية_القنوات$'))
async def disable_channel_protection(event):
    if not is_admin(await event.get_sender()): return
    channel_limits.pop(event.chat_id, None)
    save_json(CHANNEL_LIMITS_FILE, channel_limits)
    await event.reply("❌ تم تعطيل حماية القناة.")

# ---------- Global Protection ----------
@client.on(events.NewMessage())
async def global_handler(event):
    global link_protection, forward_protection, mute_duration
    if not event.raw_text or event.out: return
    chat = event.chat_id
    sender = await event.get_sender()
    if not sender or sender.id == (await client.get_me()).id: return

    if chat in channel_limits and not is_admin(sender):
        limit = channel_limits[chat]
        now_ts = time.time()
        user_msgs = user_channel_msgs[chat][sender.id]
        user_msgs[:] = [t for t in user_msgs if now_ts - t < limit["window"]]
        user_msgs.append(now_ts)
        if len(user_msgs) > limit["max_msgs"]:
            if sender.id not in mute_status or mute_status[sender.id]['until'] < now_ts:
                await mute_user(chat, sender.id, limit["window"])
                mute_status[sender.id] = {'until': now_ts + limit["window"], 'name': sender.first_name}
                last_warning = user_mute_warnings[chat][sender.id]
                if now_ts - last_warning >= limit["window"]:
                    user_mute_warnings[chat][sender.id] = now_ts
                    await client.send_message(chat, (
                        f"🚫 **انتهت فرصك يا {sender.first_name}!**\n"
                        f"📨 لقد أرسلت {limit['max_msgs']} رسائل في آخر {limit['window']//60} دقائق.\n"
                        f"⏳ يمكنك إرسال رسائل جديدة بعد {limit['window']//60} دقائق من الآن.\n"
                        f"👑 المطور: @{DEVELOPER_USERNAME}"
                    ))
            return

    if not event.is_group: return
    if chat not in active_groups: return
    if sender.username == DEVELOPER_USERNAME: return
    message_count[sender.id] += 1
    text = event.raw_text.strip()
    if link_protection and contains_link(text): await event.delete(); return
    if forward_protection and is_forward(event.message): await event.delete(); return
    if contains_swear(text.lower()):
        now = time.time(); uid = sender.id; name = sender.first_name or "مجهول"
        if uid in mute_status and mute_status[uid]['until'] > now: return
        await event.delete()
        await mute_user(chat, uid, mute_duration)
        mute_status[uid] = {'until': now + mute_duration, 'name': name}
        await event.respond(f"🚫 {name} كتم {mute_duration//60} د")

# ---------- القفل التلقائي ----------
async def auto_lock_unlock():
    global chat_locked, reminder_sent
    while True:
        if not bot_settings.get("auto_lock_enabled", False):
            await asyncio.sleep(30)
            continue
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        now_dz = now_utc + datetime.timedelta(hours=1)
        h, m = now_dz.hour, now_dz.minute
        if h == 23 and m == 30 and not reminder_sent and not chat_locked:
            reminder_sent = True
            for gid in active_groups:
                try: await client.send_message(gid, f"⚠️ تنبيه: سيتم قفل المجموعة بعد 30 دقيقة (منتصف الليل بتوقيت الجزائر).\n🔓 ستعاود الفتح الساعة 10:00 صباحاً.\n👑 @{DEVELOPER_USERNAME}")
                except: pass
        if h == 0 and m == 0 and not chat_locked:
            chat_locked = True; reminder_sent = False
            for gid in active_groups:
                try:
                    await client.edit_permissions(gid, send_messages=False)
                    await client.send_message(gid, f"🔒 تم قفل المجموعة تلقائياً – منتصف الليل.\n🌙 ستعود للفتح الساعة 10:00 صباحاً بتوقيت الجزائر.\n👑 @{DEVELOPER_USERNAME}")
                except: pass
        if h == 10 and m == 0 and chat_locked:
            chat_locked = False
            for gid in active_groups:
                try:
                    await client.edit_permissions(gid, send_messages=True)
                    await client.send_message(gid, f"🔓 تم فتح المجموعة تلقائياً – صباح الخير!\n☀️ استمتعوا بيومكم.\n👑 @{DEVELOPER_USERNAME}")
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

async def run_health_server():
    app = web.Application()
    app.router.add_get('/', handle_health)
    app.router.add_get('/api/stats', handle_api)
    app.router.add_get('/api/groups', handle_api)
    app.router.add_post('/api/broadcast', handle_api)
    app.router.add_post('/api/leave', handle_api)
    app.router.add_post('/api/globalban', handle_api)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    global BOT_PHOTO
    await client.start(bot_token=BOT_TOKEN)
    photos = await client.get_profile_photos('me', limit=1)
    if photos:
        BOT_PHOTO = InputPhoto(id=photos[0].id, access_hash=photos[0].access_hash, file_reference=photos[0].file_reference)
    print(f"✅ PIPO BOT: @{(await client.get_me()).username}")
    asyncio.create_task(auto_unmute())
    asyncio.create_task(auto_lock_unlock())
    asyncio.create_task(run_health_server())
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
