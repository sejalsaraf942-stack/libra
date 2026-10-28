# VidhiVraksh — AI Legal Awareness Assistant for India

Hackathon-ready web app. Next.js/React/TS frontend + FastAPI/Python backend + FAISS RAG.

## Run

Backend:
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp ../.env.example .env
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Health: http://localhost:8000/health

## Demo mode
With `APP_ENV=development` and `*_PROVIDER=mock`, OTP/LLM/payment are mocked and clearly labeled. No external credentials required. Mocked services are reported by /health.
