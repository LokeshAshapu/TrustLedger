# Multi-stage Dockerfile for TrustLedger

# --- Stage 1: Build Frontend SPA ---
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Build production SPA assets to dist/
RUN npm run build

# --- Stage 2: Production Python FastAPI Server ---
FROM python:3.12-slim
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Copy built frontend production bundle
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
