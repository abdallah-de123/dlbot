import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import os

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")

WAITING_MESSAGES = [
    "⏳ جاري تحميل الفيديو، انتظر شوي يا حبيب قلبي...",
    "⏳ Hold on tight, downloading your video...",
    "⏳ ثواني ثواني، الفيديو في الطريق 🚀",
    "⏳ خله يفكر شوي... yt-dlp شغال 🧠",
    "⏳ Patience is a virtue, habibi 😌",
    "⏳ جاري السحب من السيرفر، لا تستعجل علينا 😂",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً! أرسل لي رابط فيديو من يوتيوب أو تيك توك أو انستقرام وأنا بحمّله لك 🎬"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 طريقة الاستخدام:\n\n"
        "1️⃣ ارسل رابط فيديو من يوتيوب، تيك توك، أو انستقرام\n"
        "2️⃣ انتظر شوي وبيوصلك الفيديو مباشرة بالشات\n\n"
        "⚠️ ملاحظات:\n"
        "- الفيديو لازم يكون أقل من 50 ميقا\n"
        "- بعض الروابط الخاصة (Private) ما تنزل\n\n"
        "الأوامر المتوفرة:\n"
        "/start - رسالة الترحيب\n"
        "/help - هذي الرسالة"
    )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    chat_id = update.message.chat_id

    await update.message.reply_text(random.choice(WAITING_MESSAGES))

    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'format': 'best[filesize<50M]/best',
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await update.message.reply_text(
                "❌ الفيديو حجمه أكبر من 50 ميقا، وهذا حد تلقرام نفسه.\n"
                "جرّب فيديو أقصر أو بجودة أقل."
            )
            os.remove(filename)
            return

        await context.bot.send_video(chat_id=chat_id, video=open(filename, 'rb'))
        os.remove(filename)

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "unsupported url" in error_msg or "no video formats" in error_msg:
            await update.message.reply_text(
                "❌ الرابط غير مدعوم أو مو رابط فيديو صحيح.\n"
                "تأكد إنه رابط من يوتيوب، تيك توك، أو انستقرام."
            )
        elif "private" in error_msg:
            await update.message.reply_text(
                "❌ هذا الفيديو خاص (Private) وما أقدر أحمّله."
            )
        elif "429" in error_msg or "too many requests" in error_msg:
            await update.message.reply_text(
                "❌ في ضغط حالياً على الموقع، جرّب بعد شوي."
            )
        else:
            await update.message.reply_text(
                "❌ ما قدرت أحمّل الفيديو، تأكد من الرابط وحاول مرة ثانية."
            )
        if filename and os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        logging.error(f"خطأ غير متوقع: {e}")
        await update.message.reply_text(
            "❌ حصل خطأ غير متوقع، جرّب مرة ثانية بعد شوي."
        )
        if filename and os.path.exists(filename):
            os.remove(filename)

def main():
    os.makedirs('downloads', exist_ok=True)

    app = (
        Application.builder()
        .token(TOKEN)
        .read_timeout(120)
        .write_timeout(120)
        .connect_timeout(60)
        .pool_timeout(60)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    print("البوت شغّال...")
    app.run_polling()

if __name__ == "__main__":
    main()