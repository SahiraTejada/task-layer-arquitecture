#!/bin/bash

set -e

echo "🚀 Creating virtual environment..."
python -m venv venv
source .\venv\Scripts\activat

echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo "📁 Creating project structure..."
mkdir -p app
touch app/{main.py,database.py,models.py,schemas.py,crud.py}
touch .env

echo "🧬 Initializing Alembic..."
alembic init alembic

echo "📌 Making initial commit for Alembic setup..."
alembic revision --autogenerate -m "update database"

echo "📝 Updating requirements.txt with current dependecies..."
pip freeze > requirements.txt


echo "✅ Setup complete."
echo "👉 Now configure 'alembic.ini' and 'alembic/env.py' with your SQLAlchemy Base and engine."
echo "👉 Run the server using: uvicorn app.main:app --reload"
