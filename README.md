# Hospital Readmission Prediction API - Backend

FastAPI backend for hospital readmission prediction with 89% accuracy.

## Quick Start

```bash
cd backend
./setup_and_run.sh
```

Server will start at: **http://localhost:8000**

## Features

✅ Real-time readmission prediction (89% accuracy, 0.899 AUC)  
✅ Comprehensive 5-layer analysis system  
✅ Input validation (rejects invalid data)  
✅ Batch predictions (up to 100 patients)  
✅ Interactive API documentation (Swagger)  
✅ No database required (SQLite included)  
✅ CORS enabled for React/Vue/Angular

## API Endpoints

- **GET** `/` - API information
- **GET** `/health` - Health check
- **POST** `/api/v1/predictions/score` - Single prediction
- **POST** `/api/v1/predictions/batch` - Batch predictions
- **GET** `/docs` - Interactive Swagger UI
- **GET** `/redoc` - Alternative documentation

## Documentation

📖 **Full API Documentation:** [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

Includes:
- All endpoints with examples
- Request/response schemas
- React/TypeScript integration code
- Error handling
- Frontend integration guide

## Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app
│   ├── core/
│   │   └── config.py              # Configuration
│   ├── models/
│   │   └── schemas.py             # Pydantic schemas
│   ├── ml/
│   │   └── model_loader.py        # ML model loader
│   ├── services/
│   │   └── prediction_service.py  # Prediction logic
│   └── api/v1/endpoints/
│       └── predictions.py         # API endpoints
├── requirements.txt               # Python dependencies
├── setup_and_run.sh              # Setup + run script
└── README.md                     # This file
```

## Requirements

- Python 3.8+
- pip

## Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

## Configuration

Edit `.env` file:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]

# ML Model
MODEL_PATH=../best_model.pkl
```

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Single Prediction
```bash
curl -X POST http://localhost:8000/api/v1/predictions/score \
  -H "Content-Type: application/json" \
  -d @test_patient.json
```

### Interactive Testing
Visit: **http://localhost:8000/docs**

## Performance

- Prediction latency: ~45ms
- Model accuracy: 89%
- AUC: 0.899
- Supports concurrent requests

## For Frontend Developers

See **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** for:
- Complete API reference
- TypeScript types
- React integration examples
- Error handling
- Testing guide

## Support

Issues? Check:
1. Is Python 3.8+ installed? `python3 --version`
2. Is the server running? `curl http://localhost:8000/health`
3. Check logs in terminal
4. Visit http://localhost:8000/docs to test endpoints

## License

MIT
