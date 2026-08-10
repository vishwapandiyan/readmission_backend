"""
ML Model loader - singleton pattern
"""
import pickle
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path to import our existing code
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from input_validator import validate_patient_data
from comprehensive_prediction import ComprehensiveReadmissionSystem


class ModelLoader:
    """Singleton model loader"""
    _instance = None
    _model = None
    _system = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self, model_path: str):
        """Load the trained model"""
        if self._model is None:
            print(f"Loading model from {model_path}...")
            with open(model_path, 'rb') as f:
                self._model = pickle.load(f)
            print("✓ Model loaded successfully")
        return self._model
    
    def load_comprehensive_system(self, model_path: str):
        """Load the comprehensive 5-layer prediction system"""
        if self._system is None:
            print(f"Loading comprehensive system from {model_path}...")
            self._system = ComprehensiveReadmissionSystem(model_path=model_path)
            print("✓ Comprehensive system loaded successfully")
        return self._system
    
    def get_model(self):
        """Get loaded model"""
        if self._model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        return self._model
    
    def get_system(self):
        """Get comprehensive system"""
        if self._system is None:
            raise RuntimeError("System not loaded. Call load_comprehensive_system() first.")
        return self._system


# Global instance
model_loader = ModelLoader()

# Auto-load the model on startup
try:
    # Try backend directory first (for deployment)
    backend_dir = Path(__file__).parent.parent.parent
    model_path = backend_dir / "best_model.pkl"
    
    # If not found in backend dir, try parent directory (for development)
    if not model_path.exists():
        project_root = backend_dir.parent
        model_path = project_root / "best_model.pkl"
    
    if model_path.exists():
        model_loader.load_comprehensive_system(str(model_path))
        print("✓ Model auto-loaded on startup")
    else:
        print(f"⚠ Warning: Model file not found at {model_path}")
except Exception as e:
    print(f"⚠ Warning: Failed to auto-load model: {e}")
