## Fintech
Небольшой сервис для перевода средств между кошельками с защитой от race condition и асинхронными уведомлениями

---

### Сборка и запуск

```bash
docker compose build
docker compose up -d
```

После запуска сервис доступен по адресу: http://localhost:8080

### Как работает

Gunicorn используется как WSGI-сервер\

Он запускается с несколькими воркерами и потоками, что позволяет обрабатывать параллельные запросы и показать race condition

Баланс хранится в отдельной таблице + есть история всех транзакций

Защита от race condition реализована через оптимистичную блокировку с версионированием в балансе кошелька


### Генерация тестовых данных

В проекте есть management-command для создания тестовых кошельков и истории транзакций

`docker compose exec web python -m manage seed_wallets`

### Тестирование

Для тестирования написан скрипт, который параллельно выполняет x запросов
```bash
python race_test.py \
     --from-wallet af87411a-9860-4acd-a2dd-8fe3109411a9 \
     --to-wallet e329a331-7287-4466-9213-2d34f72b4c19 \ 
     --url http://localhost:8080/api/transfer/ \ 
     --amount 1001.00 \
     --requests 100
```

### API

Перевод средств

`POST /api/transfer/`\
`Idempotency-Key: str`

```json
{
  "from_wallet_id": "<uuid>",
  "to_wallet_id": "<uuid>",
  "amount": "500.00"
}
```
