# YOLO Web UI

В проекте собран готовый стек:

- `backend/` — FastAPI API для выбора модели и инференса по изображению
- `frontend/` — React/Vite интерфейс для загрузки изображения и просмотра результатов
- `telegram_bot/` — Telegram-бот с кнопкой открытия веб-интерфейса
- `models/` — ваши `.pt` веса, которые автоматически подхватываются API
- `docker-compose.yml` — запуск всего приложения через Docker Compose

## Что умеет

- показывает список всех `.pt` моделей из каталога `models/`
- принимает изображение через веб-интерфейс
- даёт выбрать `confidence`, `IoU` и `imgsz`
- возвращает картинку с боксами и список найденных объектов
- умеет отдавать ссылку на интерфейс через Telegram-бота

## Запуск через Docker Compose

Сначала создайте `.env` на основе примера:

```bash
cp .env.example .env
```

Заполните в `.env`:

```bash
TELEGRAM_BOT_TOKEN=ваш_токен_бота
WEBAPP_URL=https://ваш-публичный-домен
```

Потом запускайте:

```bash
docker compose up --build
```

После старта:

- фронтенд: `http://localhost:3000`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Telegram-бот: сервис `telegram-bot` внутри compose

## Telegram-бот

Бот отвечает на команды:

- `/start` — показывает кнопку открытия веб-интерфейса
- `/open` — повторно присылает ссылку и кнопку
- `/status` — проверяет доступность фронтенда и бэкенда

Файлы бота:

- [telegram_bot/app.py](/home/komi/web_yolo/telegram_bot/app.py)
- [telegram_bot/Dockerfile](/home/komi/web_yolo/telegram_bot/Dockerfile)

Важно: чтобы кнопка открытия сайта в Telegram работала нормально, `WEBAPP_URL` должен быть внешним `https://` адресом. `http://localhost:3000` подходит только для локального браузера на вашей машине, но не для Telegram Web App на телефоне или другом устройстве.

### Бот для открытия интерфейса

После запуска контейнеров можно открыть веб-интерфейс через маленький Python-бот:

```bash
python3 open_ui_bot.py
```

По умолчанию он ждёт `http://localhost:3000`, пока сайт станет доступен, и затем открывает его в браузере.

Если нужен другой адрес:

```bash
python3 open_ui_bot.py --url http://localhost:3000 --timeout 180
```

## Локальный запуск без Docker

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```
