"""
bot_app.py
بوت تلغرام + Flask لعمل track links مع referral + جدولة إرسال إلى المشتركين.
تأكد من وضع المتغيرات البيئية TELEGRAM_TOKEN وBASE_URL وADMIN_ID قبل التشغيل.
"""

import os
import sqlite3
import threading
import urllib.parse
from datetime import datetime, timedelta

from flask import Flask, redirect, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)

# ---------- إعدادات من البيئة ----------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "PUT_YOUR_TOKEN_HERE")
BASE_URL = os.environ.get("BASE_URL", "https://yourdomain.com")  # يجب أن يكون HTTPS
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))  # id التليجرام لصاحب البوت (للأوامر الادارية)

DB_PATH = os.environ.get("DB_PATH", "bot_data.db")
TRACK_PATH = "/track"  # endpoint التتبع

# ---------- قاعدة البيانات ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tiktok_url TEXT NOT NULL,
            owner_id INTEGER,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER,
            clicked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            referrer_id INTEGER,
            ref_code TEXT,
            ref_ip TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id INTEGER PRIMARY KEY,
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            link_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER,
            scheduled_at DATETIME,
            message_text TEXT,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def db_execute(query, params=(), fetch=False, many=False):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if many:
        c.executemany(query, params)
        conn.commit()
        conn.close()
        return None
    c.execute(query, params)
    rows = c.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return rows

# ---------- وظائف لروابط التتبع ----------
def add_link(tiktok_url, owner_id, title=""):
    db_execute("INSERT INTO links (tiktok_url, owner_id, title) VALUES (?, ?, ?)",
               (tiktok_url, owner_id, title))
    rows = db_execute("SELECT last_insert_rowid()", fetch=True)
    return rows[0][0] if rows else None

def get_link(link_id):
    rows = db_execute("SELECT id, tiktok_url, owner_id, title FROM links WHERE id=?", (link_id,), fetch=True)
    return rows[0] if rows else None

def record_click(link_id, referrer_id=None, ref_code=None, ref_ip=None):
    db_execute("INSERT INTO clicks (link_id, referrer_id, ref_code, ref_ip) VALUES (?, ?, ?, ?)",
               (link_id, referrer_id, ref_code, ref_ip))

def record_referral(referrer_id, link_id):
    db_execute("INSERT INTO referrals (referrer_id, link_id) VALUES (?, ?)", (referrer_id, link_id))

def count_clicks(link_id):
    rows = db_execute("SELECT COUNT(*) FROM clicks WHERE link_id=?", (link_id,), fetch=True)
    return rows[0][0] if rows else 0

def count_referrals_for_user(referrer_id):
    rows = db_execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (referrer_id,), fetch=True)
    return rows[0][0] if rows else 0

# ---------- مشتركين ----------
def subscribe(chat_id):
    db_execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))

def unsubscribe(chat_id):
    db_execute("DELETE FROM subscribers WHERE chat_id=?", (chat_id,))

def list_subscribers():
    rows = db_execute("SELECT chat_id FROM subscribers", fetch=True)
    return [r[0] for r in rows] if rows else []

# ---------- إنشاء رابط تتبع ----------
def make_track_link(link_id, referrer_id=None, campaign=None):
    params = {'id': link_id}
    if referrer_id:
        params['ref'] = str(referrer_id)
    if campaign:
        params['campaign'] = campaign
    return f"{BASE_URL}{TRACK_PATH}?{urllib.parse.urlencode(params)}"

# ---------- Flask app (redirect + تسجيل نقرات) ----------
flask_app = Flask(__name__)

@flask_app.route(TRACK_PATH)
def track():
    link_id = request.args.get('id')
    if not link_id:
        return "Invalid", 400
    try:
        link_id_int = int(link_id)
    except:
        return "Invalid id", 400
    ref = request.args.get('ref')  # id المحيل إن وُجد
    campaign = request.args.get('campaign', '')
    ref_ip = request.remote_addr or ''
    # سجّل النقر
    try:
        record_click(link_id_int, int(ref) if ref else None, ref_code=campaign, ref_ip=ref_ip)
        if ref:
            # سجّل إحالة (يمكن تحسين شرط الإحالة لمنع التكرار)
            record_referral(int(ref), link_id_int)
    except Exception as e:
        # لا نوقف إعادة التوجيه لو فشل التسجيل
        print("DB error:", e)
    # إعادة التوجيه إلى تيك توك (أو صفحة هبوط)
    ln = get_link(link_id_int)
    if not ln:
        return "Not found", 404
    dest = ln[1]
    # أضف UTM بسيط حتى تستطيع رؤية المصدر في تحليلات تيك توك/الويب إذا رغبت
    parsed = urllib.parse.urlparse(dest)
    q = dict(urllib.parse.parse_qsl(parsed.query))
    q.update({'utm_source': 'telegram_bot', 'utm_campaign': campaign or 'bot_share'})
    newq = urllib.parse.urlencode(q)
    dest_with_utm = urllib.parse.urlunparse(parsed._replace(query=newq))
    return redirect(dest_with_utm, code=302)

# ---------- Telegram Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = ("أهلاً! أنا بوت ترويج شرعي للفيديوهات.\n\n"
           "أرسل رابط تيك توك هنا لأضيفه للنشر تلقائياً (أو استخدم /subscribe للاشتراك في التنبيهات).")
    await update.message.reply_text(txt)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = ("/start - بدء\n"
           "/subscribe - اشترك لتصلك روابط الفيديو الجديدة\n"
           "/unsubscribe - إلغاء الاشتراك\n"
           "أرسل رابط تيك توك لحفظه ونشره.\n"
           "/myref - احصل على رابط الإحالة الخاص بك\n"
           "/mylinks - روابطك المحفوظة\n")
    await update.message.reply_text(txt)

async def subscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribe(update.effective_chat.id)
    await update.message.reply_text("تم الاشتراك — ستصلك إشعارات عند نشر روابط جديدة (لا سبام).")

async def unsubscribe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    unsubscribe(update.effective_chat.id)
    await update.message.reply_text("تم إلغاء الاشتراك.")

async def myref_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # أنشئ رابط إحالة عام (يرتبط بنشر أي رابط لاحق عبر البوت)
    # هنا نستخدم رابط عام يشير فقط إلى صفحة الهبوط الرئيسية أو لصفحة 'about' إذا رغبت
    # لكن الأفضل أن يعطي المستخدم صندوقًا نسخًا لإرفاق ref عند مشاركة كل رابط
    txt = ("للحصول على إحالات صالحة: عند مشاركة كل رابط استخدم زر المشاركة داخل البوت — "
           "ستُضاف معرفك كمحيل تلقائياً.\n\n"
           f"عدد الإحالات المسجلة لديك: {count_referrals_for_user(user_id)}")
    await update.message.reply_text(txt)

async def mylinks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rows = db_execute("SELECT id, tiktok_url, title, created_at FROM links WHERE owner_id=? ORDER BY created_at DESC",
                      (uid,), fetch=True)
    if not rows:
        await update.message.reply_text("لا توجد روابط محفوظة باسمك.")
        return
    out = []
    for r in rows:
        link_id, url, title, created = r
        track = make_track_link(link_id, referrer_id=uid)
        out.append(f"#{link_id} — {title or url}\n{track}\nنقرات: {count_clicks(link_id)}\n")
    await update.message.reply_text("\n\n".join(out))

async def new_link_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    # تحقق بسيط إن كان رابط تيك توك
    if 'tiktok.com' in text or 'vm.tiktok.com' in text:
        link_id = add_link(text, update.effective_user.id, title='')
        # أنشئ رابط التتبع العام (بدون ref)
        track_link = make_track_link(link_id)
        # رابط مشاركة جاهز يستخدم واجهة مشاركة تلغرام
        share_text = urllib.parse.quote_plus(f"شاهد هذا الفيديو: {track_link}\nادعم المحتوى باللايك والتعليق!")
        tg_share_url = f"https://t.me/share/url?url={urllib.parse.quote_plus(track_link)}&text={share_text}"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("شاهد الآن (تتبع)", url=track_link)],
            [InlineKeyboardButton("شارك بسرعة (زر مشاركة)", url=tg_share_url)]
        ])
        await update.message.reply_text(
            f"تم حفظ الرابط. رابط التتبع:\n{track_link}\n\nإحصائيات ستظهر بعد النقرات.",
            reply_markup=keyboard
        )
        # أرسل إشعار للمشتركين (يمكن تعديل المحتوى)
        subs = list_subscribers()
        for chat_id in subs:
            try:
                # لكل مشترك نُدرج ref = chat_id حتى تسجل الإحالة عند النقر
                user_track = make_track_link(link_id, referrer_id=chat_id)
                share_text_user = urllib.parse.quote_plus(f"شاهد هذا الفيديو: {user_track}\nلا تنسَ اللايك!")
                tg_share_user = f"https://t.me/share/url?url={urllib.parse.quote_plus(user_track)}&text={share_text_user}"
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("شاهد الفيديو", url=user_track)],
                    [InlineKeyboardButton("شارك مع أصدقائك", url=tg_share_user)]
                ])
                await context.bot.send_message(chat_id=chat_id,
                                               text=f"فيديو جديد من @{update.effective_user.username or update.effective_user.first_name}",
                                               reply_markup=kb)
            except Exception as e:
                print("send error to subscriber", e)
    else:
        await update.message.reply_text("أرسل رابط تيك توك صالح لنتمكن من حفظه ومشاركته.")

# ---------- أوامر إدارية (الجدولة والبث) ----------
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("غير مصرح.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("استخدام: /broadcast <link_id> <نص اختياري>")
        return
    link_id = int(args[0])
    message_text = " ".join(args[1:])
    subs = list_subscribers()
    sent = 0
    for chat in subs:
        try:
            user_track = make_track_link(link_id, referrer_id=chat)
            share_text_user = urllib.parse.quote_plus(f"{message_text}\n{user_track}")
            tg_share_user = f"https://t.me/share/url?url={urllib.parse.quote_plus(user_track)}&text={share_text_user}"
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("شاهد الفيديو", url=user_track)],
                [InlineKeyboardButton("شارك", url=tg_share_user)]
            ])
            await context.bot.send_message(chat_id=chat, text=message_text, reply_markup=kb)
            sent += 1
        except Exception as e:
            print("broadcast error", e)
    await update.message.reply_text(f"تم الإرسال إلى {sent} مشترك(ين).")

async def schedule_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /schedule <link_id> <YYYY-MM-DD_HH:MM> <نص>
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("غير مصرح.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("استخدام: /schedule <link_id> <YYYY-MM-DD_HH:MM> <نص>")
        return
    link_id = int(context.args[0])
    dt_str = context.args[1]
    message_text = " ".join(context.args[2:])
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d_%H:%M")
    except:
        await update.message.reply_text("صيغة التاريخ خاطئة. استخدم YYYY-MM-DD_HH:MM")
        return
    db_execute("INSERT INTO scheduled_jobs (link_id, scheduled_at, message_text, created_by) VALUES (?, ?, ?, ?)",
               (link_id, dt.isoformat(), message_text, update.effective_user.id))
    await update.message.reply_text("تم جدولة الإرسال.")
    # ستتم معالجتها بواسطة الـ scheduler أدناه

# ---------- معالجة الوظائف المجدولة بواسطة APScheduler ----------
scheduler = BackgroundScheduler()

def job_send_scheduled():
    now = datetime.utcnow()
    rows = db_execute("SELECT id, link_id, scheduled_at, message_text FROM scheduled_jobs WHERE scheduled_at <= ?",
                      (now.isoformat(),), fetch=True)
    if not rows:
        return
    for job in rows:
        job_id, link_id, sched_at, msg_text = job
        subs = list_subscribers()
        sent = 0
        for chat in subs:
            try:
                user_track = make_track_link(link_id, referrer_id=chat)
                share_text_user = urllib.parse.quote_plus(f"{msg_text}\n{user_track}")
                tg_share_user = f"https://t.me/share/url?url={urllib.parse.quote_plus(user_track)}&text={share_text_user}"
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("شاهد الفيديو", url=user_track)],
                    [InlineKeyboardButton("شارك", url=tg_share_user)]
                ])
                # نستخدم بوت هنا عبر واجهة API خارجية: نضع مهمة لإرسال الرسائل عبر التطبيق الرئيسي (see send_job below)
                # لكن لأن هذا يعمل في نفس العملية، سن استدعاء send عبر مكتبة telegram (سنوفر دالة خارجية لاحقاً)
                from telegram import Bot
                bot = Bot(token=TELEGRAM_TOKEN)
                bot.send_message(chat_id=chat, text=msg_text, reply_markup=kb)
                sent += 1
            except Exception as e:
                print("scheduled send error", e)
        # بعد الإرسال احذف الوظيفة من الجدول
        db_execute("DELETE FROM scheduled_jobs WHERE id=?", (job_id,))
        print(f"Scheduled job {job_id} sent to {sent} subscribers.")

# شغّل الـ scheduler كل دقيقة لتفقد المهام
scheduler.add_job(job_send_scheduled, 'interval', seconds=60)
scheduler.start()

# ---------- تشغيل Flask و Telegram معاً ----------
def run_flask():
    # في الإنتاج تأكد من تشغيل Flask عبر WSGI (gunicorn) ووجود HTTPS
    flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

async def main():
    init_db()
    # شغّل Flask في ثريد منفصل
    threading.Thread(target=run_flask, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("subscribe", subscribe_cmd))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe_cmd))
    app.add_handler(CommandHandler("myref", myref_cmd))
    app.add_handler(CommandHandler("mylinks", mylinks_cmd))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    app.add_handler(CommandHandler("schedule", schedule_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, new_link_message))
    print("Bot started (polling)...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
