"""
Prediction service - handles all prediction logic
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from uuid import uuid4
from datetime import datetime

from app.models.schemas import (
    PatientFeatures,
    ComprehensivePrediction,
    Layer1Prediction,
    Layer2RiskLevel,
    Layer3Explanation,
    Layer4TimeEstimate,
    Layer5Interventions,
    RiskFactor,
    Recommendation,
    RiskTier,
    Priority
)
from app.ml.model_loader import model_loader


class PredictionService:
    """Service for making predictions"""
    
    def __init__(self):
        self.system = model_loader.get_system()
    
    def predict(self, features: PatientFeatures) -> ComprehensivePrediction:
        """
        Make comprehensive 5-layer prediction
        """
        # Convert Pydantic model to DataFrame
        features_dict = features.model_dump()
        df = pd.DataFrame([features_dict])
        
        # Make prediction using comprehensive system
        results = self.system.predict(df)
        
        if results is None:
            raise ValueError("Prediction failed - invalid input data")
        
        # Convert results to API schema
        prediction = self._convert_to_schema(results, 0)
        prediction.prediction_id = str(uuid4())
        prediction.timestamp = datetime.now()
        
        return prediction
    
    def batch_predict(self, features_list: List[PatientFeatures]) -> List[ComprehensivePrediction]:
        """
        Make predictions for multiple patients
        """
        # Convert to DataFrame
        features_dicts = [f.model_dump() for f in features_list]
        df = pd.DataFrame(features_dicts)
        
        # Make batch prediction
        results = self.system.predict(df)
        
        if results is None:
            raise ValueError("Batch prediction failed - invalid input data")
        
        # Convert all results to schema
        predictions = []
        for i in range(len(features_list)):
            pred = self._convert_to_schema(results, i)
            pred.prediction_id = str(uuid4())
            pred.timestamp = datetime.now()
            predictions.append(pred)
        
        return predictions
    
    def _convert_to_schema(self, results: Dict, index: int) -> ComprehensivePrediction:
        """Convert comprehensive system results to API schema"""
        
        # Layer 1
        layer1_data = results['layer1_prediction'].iloc[index]
        layer1 = Layer1Prediction(
            will_readmit=layer1_data['will_readmit'],
            probability=float(layer1_data['probability']),
            confidence=layer1_data['confidence']
        )
        
        # Layer 2
        layer2_data = results['layer2_risk_level'].iloc[index]
        layer2 = Layer2RiskLevel(
            risk_tier=RiskTier(str(layer2_data['risk_tier'])),
            urgency=layer2_data['urgency'],
            probability_range=layer2_data['probability_range']
        )
        
        # Layer 3
        layer3_data = results['layer3_why'][index]
        layer3 = Layer3Explanation(
            risk_factors=[
                RiskFactor(
                    feature=rf['feature'],
                    contribution=rf['contribution'],
                    impact=rf['impact']
                ) for rf in layer3_data['risk_factors']
            ],
            protective_factors=[
                RiskFactor(
                    feature=pf['feature'],
                    contribution=pf['contribution'],
                    impact=pf['impact']
                ) for pf in layer3_data['protective_factors']
            ],
            risk_profile=layer3_data['risk_profile']
        )
        
        # Layer 4
        layer4_data = results['layer4_when'].iloc[index]
        layer4 = Layer4TimeEstimate(
            day7_risk=float(layer4_data['7_day_risk']),
            day30_risk=float(layer4_data['30_day_risk']),
            day90_risk=float(layer4_data['90_day_risk']),
            most_likely_window=layer4_data['most_likely_window'],
            note=layer4_data['note']
        )
        
        # Layer 5
        layer5_data = results['layer5_intervention'][index]
        layer5 = Layer5Interventions(
            recommendations=[
                Recommendation(
                    priority=Priority(rec['priority']),
                    intervention=rec['intervention'],
                    rationale=rec['rationale']
                ) for rec in layer5_data['recommendations']
            ]
        )
        
        return ComprehensivePrediction(
            layer1_prediction=layer1,
            layer2_risk_level=layer2,
            layer3_why=layer3,
            layer4_when=layer4,
            layer5_intervention=layer5
        )


# Global instance
prediction_service = PredictionService()
