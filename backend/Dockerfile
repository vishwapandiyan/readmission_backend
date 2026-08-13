FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Copy ML model files from parent directory
COPY ../best_model.pkl /app/best_model.pkl
COPY ../best_model_feature_importance.csv /app/best_model_feature_importance.csv
COPY ../comprehensive_prediction.py /app/comprehensive_prediction.py
COPY ../input_validator.py /app/input_validator.py

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
