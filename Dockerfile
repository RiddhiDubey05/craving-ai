# ==========================================
# Build React/Static Frontend (Optional if pre-built, but good practice)
# ==========================================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
# Note: since this is vanilla JS/HTML, we don't actually need to build it,
# but setting up a stage in case we migrate to React/Vite later.
COPY frontend/ ./
# If package.json exists: RUN npm install && npm run build

# ==========================================
# Build Backend
# ==========================================
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for FAISS, SQLite, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy frontend static files to be served by FastAPI
COPY --from=frontend-builder /app/frontend/ ./frontend/

# Expose port
EXPOSE 8000

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8000

# Run FastAPI server using Uvicorn
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
