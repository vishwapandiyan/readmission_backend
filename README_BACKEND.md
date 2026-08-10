# Hospital Readmission Prediction - Backend API

FastAPI backend for the Hospital Readmission Prediction System with comprehensive 5-layer risk assessment.

## 🚀 Features

- **Real-time ML Predictions** - 89% accuracy, 0.899 AUC
- **5-Layer Analysis System**:
  - Layer 1: Binary prediction + probability + confidence
  - Layer 2: Risk tier classification (Low/Moderate/High/Critical)
  - Layer 3: Risk factors and explanations
  - Layer 4: Timeline predictions (7/30/90-day risks)
  - Layer 5: Prioritized intervention recommendations
- **Input Validation** - Comprehensive clinical range validation
- **Batch Predictions** - Process up to 100 patients at once
- **Auto-documentation** - Swagger UI and ReDoc
- **No Database Required** - Works immediately after setup

## 📋 Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

## 🛠️ Installation

### Option 1: Automated Setup (Recommended)

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

### Option 2: Manual Setup

1. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Ensure model file exists**
The system expects `best_model.pkl` in the parent directory:
```
Readmission system/
├── backend/
│   └── (backend files)
└── best_model.pkl  ← Model file here
```

4. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🌐 API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/api/v1/predictions/score` | Single patient prediction |
| POST | `/api/v1/predictions/batch` | Batch predictions (max 100) |
| GET | `/docs` | Interactive API docs (Swagger) |
| GET | `/redoc` | Alternative API docs |

## 📝 API Usage Examples

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_loaded": true,
  "timestamp": "2026-08-10T14:30:00"
}
```

### Single Prediction

```bash
curl -X POST http://localhost:8000/api/v1/predictions/score \
  -H "Content-Type: application/json" \
  -d '{
    "age": 65,
    "sex": 1,
    "bmi": 28.5,
    "insurance_type": "Medicare",
    "comorbidity_index": 3,
    "diabetes_flag": 1,
    "heart_failure_flag": 0,
    "copd_flag": 0,
    "ckd_flag": 0,
    "cancer_flag": 0,
    "dementia_flag": 0,
    "previous_admissions_12m": 2,
    "previous_er_visits_12m": 1,
    "prior_30_day_readmission_flag": 0,
    "admission_type": "emergency",
    "length_of_stay_days": 5,
    "icu_stay_flag": 1,
    "discharge_destination": "home",
    "medication_count_at_discharge": 8,
    "polypharmacy_flag": 1,
    "high_risk_medication_flag": 1,
    "hemoglobin": 12.5,
    "creatinine": 1.2,
    "glucose": 145,
    "hbA1c": 7.2,
    "wbc_count": 8.5,
    "total_bilirubin": 0.8,
    "follow_up_within_7_days_flag": 1,
    "total_charges_index_stay": 25000
  }'
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── predictions.py    # Prediction endpoints
│   │       └── router.py              # API router
│   ├── core/
│   │   └── config.py                  # Configuration
│   ├── ml/
│   │   └── model_loader.py            # ML model loader
│   ├── models/
│   │   └── schemas.py                 # Pydantic schemas
│   ├── services/
│   │   └── prediction_service.py      # Business logic
│   ├── utils/
│   └── main.py                        # FastAPI app
├── requirements.txt                   # Python dependencies
├── setup_and_run.sh                  # Setup script
├── run.sh                            # Run script
└── README_BACKEND.md                 # This file
```

## 🔧 Configuration

Edit `app/core/config.py` to customize:

- **CORS Origins** - Add your frontend URL
- **API Settings** - Title, version, description
- **Model Path** - Change model file location

## 📊 Model Information

- **Algorithm**: Logistic Regression
- **Training Data**: 6,000 patients
- **Features**: 29 clinical and demographic variables
- **Performance**: 
  - Accuracy: 89.0%
  - AUC: 0.899
  - Optimized for clinical use

## 🧪 Testing

### Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Test prediction (see test_patient.json)
curl -X POST http://localhost:8000/api/v1/predictions/score \
  -H "Content-Type: application/json" \
  -d @test_patient.json
```

### Interactive Testing

Visit http://localhost:8000/docs for Swagger UI where you can:
- Try all endpoints interactively
- See request/response schemas
- Test with example data

## 🔒 Security

- CORS enabled for specified origins
- Input validation on all fields
- Clinical range checks
- No sensitive data logging

## 🐛 Troubleshooting

### Model not found

**Error**: `FileNotFoundError: Model file not found`

**Solution**: Ensure `best_model.pkl` is in the parent directory:
```bash
ls ../best_model.pkl
```

### Import errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**: Run from the backend directory:
```bash
cd backend
uvicorn app.main:app --reload
```

### Port already in use

**Error**: `Address already in use`

**Solution**: Use a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## 📦 Dependencies

Key packages:
- **FastAPI** - Modern web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Pandas** - Data manipulation
- **Scikit-learn** - ML model
- **Pickle** - Model serialization

See `requirements.txt` for complete list.

## 🚢 Deployment

### Docker (Coming Soon)

```bash
docker build -t readmission-api .
docker run -p 8000:8000 readmission-api
```

### Production

For production deployment:

1. Use production ASGI server:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

2. Set environment variables:
```bash
export DEBUG=False
export HOST=0.0.0.0
export PORT=8000
```

3. Add authentication/authorization as needed
4. Use HTTPS with reverse proxy (nginx/Apache)
5. Set up monitoring and logging

## 📄 License

MIT License - See LICENSE file for details

## 👥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For issues or questions:
- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the comprehensive prediction system in `comprehensive_prediction.py`

## 🔗 Related Projects

- **Frontend**: React TypeScript application (separate repository)
- **Model Training**: See `train_model.py` in parent directory
- **Data Validation**: See `input_validator.py` in parent directory

---

**Built with ❤️ for better patient outcomes**
