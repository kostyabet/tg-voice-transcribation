#!/usr/bin/env python3
"""
Telegram-бот для транскрипции голосовых сообщений с помощью локального Whisper.
"""

import asyncio
import logging
import os
import tempfile

import whisper
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Глобальная модель Whisper (загружается один раз при старте).
whisper_model = None


def load_whisper_model(model_name: str = "base"):
    """Загружает модель Whisper (один раз при старте)."""
    global whisper_model
    if whisper_model is None:
        logger.info("Загрузка модели Whisper '%s'...", model_name)
        whisper_model = whisper.load_model(model_name)
        logger.info("Модель загружена.")
    return whisper_model


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    await update.message.reply_text(
        "Привет! Отправь мне голосовое сообщение или кружочек "
        "(свой или пересланный), и я расшифрую его в текст с помощью Whisper."
    )


async def transcribe_telegram_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    file_id: str,
    status_text: str,
) -> None:
    """Скачивает медиа по file_id и возвращает распознанный текст."""
    if not update.message:
        return

    message = update.message
    status_msg = await message.reply_text(status_text)

    try:
        file = await context.bot.get_file(file_id)

        suffix = ".ogg" if file.file_path and file.file_path.endswith(".ogg") else ".mp4"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name

        try:
            await file.download_to_drive(tmp_path)

            # Транскрипция в отдельном потоке (Whisper блокирующий).
            loop = asyncio.get_running_loop()
            model = load_whisper_model(os.environ.get("WHISPER_MODEL", "base"))
            result = await loop.run_in_executor(
                None,
                lambda: model.transcribe(tmp_path, fp16=False, language=None),
            )

            text = result.get("text", "").strip()

            if text:
                await status_msg.edit_text(f"📝 Текст сообщения:\n\n{text}")
            else:
                await status_msg.edit_text(
                    "Не удалось распознать речь. Попробуйте записать более "
                    "чётко или ближе к микрофону."
                )
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.exception("Ошибка при обработке медиа-сообщения")
        await status_msg.edit_text(f"❌ Ошибка при расшифровке: {e}")


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик голосовых сообщений."""
    if not update.message or not update.message.voice:
        return
    await transcribe_telegram_file(
        update,
        context,
        file_id=update.message.voice.file_id,
        status_text="⏳ Обрабатываю голосовое сообщение...",
    )


async def video_note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кружочков (video_note)."""
    if not update.message or not update.message.video_note:
        return
    await transcribe_telegram_file(
        update,
        context,
        file_id=update.message.video_note.file_id,
        status_text="⏳ Обрабатываю кружочек...",
    )


def main() -> None:
    """Запуск бота."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Ошибка: задайте переменную окружения TELEGRAM_BOT_TOKEN")
        print("Проще всего — создать файл .env (см. .env.example):")
        print("  TELEGRAM_BOT_TOKEN=your_bot_token_here")
        return

    # Предзагрузка модели при старте.
    load_whisper_model(os.environ.get("WHISPER_MODEL", "base"))

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, video_note_handler))

    logger.info("Бот запущен.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
