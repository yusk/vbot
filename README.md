# vbot

## setup

```bash
poetry install
cp .env.sample .env
vim .env
```

## run local

```bash
poetry run uvicorn server:app --reload
ngrok http 8000
```
