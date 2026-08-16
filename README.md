# Parrot School Admin Bot

Telegram бот для отримання заявок з сайту Parrot School.

## Railway Variables

```
BOT_TOKEN=токен_від_botfather
ADMIN_CHAT_ID=твій_telegram_id
WEBHOOK_SECRET=parrot2026
PORT=8000
```

## Як дізнатись ADMIN_CHAT_ID

Напиши @userinfobot в Telegram — він покаже твій ID.

## Endpoint для форми на сайті

```
POST https://your-railway-url/form
Content-Type: application/json

{
  "secret": "parrot2026",
  "type": "Безкоштовний урок",
  "name": "Ім'я батьків",
  "phone": "+380991234567",
  "child_age": "8",
  "message": "Хочу записатись"
}
```

## Команди бота

- `/start` — привітання
- `/status` — перевірка роботи
- `/test` — тестова заявка
