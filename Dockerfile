# Multi-stage Dockerfile for Forensic Engine
# Backend Build
FROM python:3.11-slim AS backend
WORKDIR /app
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Note: Frontend usually deployed to Vercel, but for Docker:
# FROM node:20-slim AS frontend
# ...
