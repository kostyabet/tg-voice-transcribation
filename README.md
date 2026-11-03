# tg-voice-transcribation

Локальный Telegram-бот, который расшифровывает голосовые сообщения и кружочки
(video note) в текст с помощью [Whisper](https://github.com/openai/whisper).
Всё работает на твоей машине — аудио никуда не уходит, кроме серверов Telegram.

## Требования

- Python 3.9+
- `ffmpeg` (Whisper использует его для декодирования аудио)

Проверить ffmpeg: `which ffmpeg`. Если нет — `brew install ffmpeg` (macOS).

## Установка

```bash
# 1. Виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Зависимости
pip install -r requirements.txt

# 3. Конфиг
cp .env.example .env
# затем открой .env и вставь токен от @BotFather
```

### Где взять токен

1. В Telegram напиши [@BotFather](https://t.me/BotFather) → `/newbot`.
2. Задай имя и username бота.
3. BotFather пришлёт токен вида `123456789:AA...` — вставь его в `.env`
   в поле `TELEGRAM_BOT_TOKEN`.

## Запуск

```bash
source .venv/bin/activate
python bot.py
```

При первом запуске Whisper скачает файл модели (`base` ≈ 140 МБ) —
это одноразово. Дальше напиши боту `/start` и отправь голосовое или кружочек.

## Выбор модели

Через `WHISPER_MODEL` в `.env`:

| Модель  | Размер | Качество | Скорость |
|---------|--------|----------|----------|
| tiny    | ~75 МБ | низкое   | очень быстро |
| base    | ~140 МБ| среднее  | быстро |
| small   | ~460 МБ| хорошее  | средне |
| medium  | ~1.5 ГБ| высокое  | медленно |
| large   | ~3 ГБ  | лучшее   | очень медленно |

Для русской речи `small` заметно точнее `base`, если машина тянет.

## Деплой

Чтобы бот работал постоянно — два варианта.

### Вариант A: Docker (рекомендуется)

ffmpeg уже внутри образа, модель Whisper кэшируется в volume `whisper-cache`
(не качается при каждой пересборке).

```bash
cp .env.example .env    # вставь токен
docker compose up -d --build
docker compose logs -f  # посмотреть логи
```

Обновить после изменений кода: `docker compose up -d --build`.
Остановить: `docker compose down`.

### Вариант B: systemd (без Docker)

Запуск прямо из venv на Linux-сервере.

```bash
# 1. Разложи проект и зависимости
sudo mkdir -p /opt/tg-voice-transcribation
sudo cp -r bot.py requirements.txt .env /opt/tg-voice-transcribation/
cd /opt/tg-voice-transcribation
sudo apt install -y ffmpeg
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 2. Юнит (поправь User/пути внутри файла при необходимости)
sudo cp deploy/tg-voice-transcribation.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now tg-voice-transcribation
sudo journalctl -u tg-voice-transcribation -f   # логи
```

## Заметки

- Бот обрабатывает сообщения последовательно: пока идёт одна расшифровка,
  следующая ждёт. Для личного использования этого достаточно.
- `.env` в `.gitignore` — токен не попадёт в git.
