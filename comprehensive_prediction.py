"""
Comprehensive Hospital Readmission Prediction System
-----------------------------------------------------
A 5-layer system that provides:
1. Will the patient be readmitted? (YES/NO + probability)
2. How likely is readmission? (Risk tier)
3. Why is this patient high risk? (Feature contributions)
4. When is readmission most likely? (Time-based risk if available)
5. What intervention should be considered? (Actionable recommendations)

Usage:
    from comprehensive_prediction import ComprehensiveReadmissionSystem
    
    system = ComprehensiveReadmissionSystem()
    results = system.predict(patient_data)
    system.print_patient_report(results, patient_index=0)
"""

import pandas as pd
import numpy as np
import pickle
from typing import Dict, List, Tuple
from input_validator import validate_patient_data

class ComprehensiveReadmissionSystem:
    """
    Complete readmission prediction system with explainability
    """
    
    def __init__(self, model_path: str = 'best_model.pkl'):
        """Load model and feature importance"""
        print("Initializing Comprehensive Readmission Prediction System...")
        
        # Load model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
        print(f"✓ Model loaded: {model_path}")
        
        # Load feature importance
        try:
            self.feature_importance = pd.read_csv('best_model_feature_importance.csv')
            print(f"✓ Feature importance loaded")
        except:
            self.feature_importance = None
            print("⚠️  Feature importance not found (explanation will be limited)")
        
        print("✓ System ready\n")
    
    def predict(self, patient_data: pd.DataFrame) -> Dict:
        """
        Comprehensive prediction with all 5 layers
        
        Returns dictionary with:
        - Layer 1: Binary prediction + probability
        - Layer 2: Risk tier categorization
        - Layer 3: Feature contributions (why)
        - Layer 4: Time-based risk (if available)
        - Layer 5: Intervention recommendations
        """
        # Validate input
        is_valid, errors = validate_patient_data(patient_data)
        if not is_valid:
            print("❌ VALIDATION FAILED")
            for error in errors:
                if error.startswith("❌"):
                    print(f"  {error}")
            return None
        
        # Get predictions
        probabilities = self.model.predict_proba(patient_data)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)
        
        # Build comprehensive results
        results = {
            'layer1_prediction': self._layer1_will_readmit(predictions, probabilities),
            'layer2_risk_level': self._layer2_risk_level(probabilities),
            'layer3_why': self._layer3_explain_risk(patient_data, probabilities),
            'layer4_when': self._layer4_time_prediction(probabilities),
            'layer5_intervention': self._layer5_interventions(probabilities, patient_data),
            'raw_data': {
                'predictions': predictions,
                'probabilities': probabilities,
                'patient_data': patient_data
            }
        }
        
        return results
    
    def _layer1_will_readmit(self, predictions: np.ndarray, probabilities: np.ndarray) -> pd.DataFrame:
        """
        Layer 1: Will the patient be readmitted?
        Binary prediction + probability
        """
        return pd.DataFrame({
            'will_readmit': ['YES' if p == 1 else 'NO' for p in predictions],
            'probability': probabilities,
            'confidence': ['High' if abs(p - 0.5) > 0.3 else 'Medium' if abs(p - 0.5) > 0.15 else 'Low' 
                          for p in probabilities]
        })
    
    def _layer2_risk_level(self, probabilities: np.ndarray) -> pd.DataFrame:
        """
        Layer 2: How likely is readmission?
        Risk tier categorization
        """
        risk_tiers = pd.cut(
            probabilities,
            bins=[0, 0.10, 0.30, 0.60, 1.0],
            labels=['Low', 'Moderate', 'High', 'Critical']
        )
        
        urgency = []
        for tier in risk_tiers:
            if tier == 'Critical':
                urgency.append('URGENT - Immediate intervention required')
            elif tier == 'High':
                urgency.append('HIGH - Intensive care coordination needed')
            elif tier == 'Moderate':
                urgency.append('MODERATE - Standard follow-up recommended')
            else:
                urgency.append('LOW - Routine discharge protocol')
        
        return pd.DataFrame({
            'risk_tier': risk_tiers,
            'urgency': urgency,
            'probability_range': [f"{probabilities[i]:.0%}" for i in range(len(probabilities))]
        })
    
    def _layer3_explain_risk(self, patient_data: pd.DataFrame, probabilities: np.ndarray) -> List[Dict]:
        """
        Layer 3: Why is this patient high risk?
        Feature-based explanation
        """
        explanations = []
        
        # Get feature names from model
        feature_names = self.model.named_steps['prep'].get_feature_names_out()
        
        # Transform patient data through preprocessing
        X_transformed = self.model.named_steps['prep'].transform(patient_data)
        
        # Get model coefficients (for Logistic Regression)
        if hasattr(self.model.named_steps['clf'], 'coef_'):
            coefficients = self.model.named_steps['clf'].coef_[0]
            
            for i in range(len(patient_data)):
                # Calculate contribution of each feature
                contributions = X_transformed[i] * coefficients
                
                # Get top contributing features
                top_indices = np.argsort(np.abs(contributions))[-10:][::-1]
                
                risk_factors = []
                protective_factors = []
                
                for idx in top_indices:
                    feat_name = feature_names[idx]
                    contribution = contributions[idx]
                    
                    # Clean up feature name
                    clean_name = self._clean_feature_name(feat_name)
                    
                    if abs(contribution) > 0.05:  # Only significant contributions
                        if contribution > 0:
                            risk_factors.append({
                                'feature': clean_name,
                                'contribution': float(contribution),
                                'impact': 'Increases risk'
                            })
                        else:
                            protective_factors.append({
                                'feature': clean_name,
                                'contribution': float(abs(contribution)),
                                'impact': 'Decreases risk'
                            })
                
                # Create risk profile
                risk_profile = self._create_risk_profile(patient_data.iloc[i])
                
                explanations.append({
                    'risk_factors': risk_factors[:5],  # Top 5
                    'protective_factors': protective_factors[:3],  # Top 3
                    'risk_profile': risk_profile
                })
        else:
            # If not logistic regression, provide basic explanation
            for i in range(len(patient_data)):
                explanations.append({
                    'risk_factors': [{'feature': 'Model type does not support feature importance', 
                                     'contribution': 0, 'impact': 'N/A'}],
                    'protective_factors': [],
                    'risk_profile': self._create_risk_profile(patient_data.iloc[i])
                })
        
        return explanations
    
    def _layer4_time_prediction(self, probabilities: np.ndarray) -> pd.DataFrame:
        """
        Layer 4: When is readmission most likely?
        Time-based risk estimation (simplified - actual requires survival analysis)
        """
        # Note: This is a simplified version. True time-to-event prediction 
        # requires survival analysis (Cox model, etc.) and time-to-readmission data
        
        time_predictions = []
        for prob in probabilities:
            # Heuristic-based estimation (would need proper survival model in production)
            if prob > 0.8:
                time_predictions.append({
                    '7_day_risk': min(prob * 0.6, 1.0),  # High early risk
                    '30_day_risk': prob,
                    '90_day_risk': min(prob * 1.1, 1.0),
                    'most_likely_window': '0-14 days (early readmission)',
                    'note': 'Very high risk patients often readmit within 2 weeks'
                })
            elif prob > 0.6:
                time_predictions.append({
                    '7_day_risk': prob * 0.4,
                    '30_day_risk': prob,
                    '90_day_risk': min(prob * 1.15, 1.0),
                    'most_likely_window': '7-30 days',
                    'note': 'High risk patients typically readmit within first month'
                })
            elif prob > 0.3:
                time_predictions.append({
                    '7_day_risk': prob * 0.3,
                    '30_day_risk': prob,
                    '90_day_risk': min(prob * 1.2, 1.0),
                    'most_likely_window': '14-60 days',
                    'note': 'Moderate risk spread across post-discharge period'
                })
            else:
                time_predictions.append({
                    '7_day_risk': prob * 0.2,
                    '30_day_risk': prob,
                    '90_day_risk': prob * 1.1,
                    'most_likely_window': 'Evenly distributed',
                    'note': 'Low overall risk'
                })
        
        return pd.DataFrame(time_predictions)
    
    def _layer5_interventions(self, probabilities: np.ndarray, patient_data: pd.DataFrame) -> List[Dict]:
        """
        Layer 5: What intervention should be considered?
        Actionable recommendations based on risk and patient characteristics
        """
        interventions = []
        
        for i, prob in enumerate(probabilities):
            patient = patient_data.iloc[i]
            recommendations = []
            
            # Risk-based interventions
            if prob > 0.8:
                recommendations.append({
                    'priority': 'URGENT',
                    'intervention': 'Assign to dedicated care team',
                    'rationale': f'{prob:.0%} risk - highest priority'
                })
                recommendations.append({
                    'priority': 'URGENT',
                    'intervention': 'Schedule follow-up within 48 hours',
                    'rationale': 'Early intervention critical'
                })
            elif prob > 0.6:
                recommendations.append({
                    'priority': 'HIGH',
                    'intervention': 'Intensive case management',
                    'rationale': f'{prob:.0%} risk - needs close monitoring'
                })
                recommendations.append({
                    'priority': 'HIGH',
                    'intervention': 'Schedule follow-up within 7 days',
                    'rationale': 'Early detection of issues'
                })
            elif prob > 0.3:
                recommendations.append({
                    'priority': 'MODERATE',
                    'intervention': 'Standard care coordination',
                    'rationale': f'{prob:.0%} risk - routine follow-up needed'
                })
            else:
                recommendations.append({
                    'priority': 'LOW',
                    'intervention': 'Routine discharge protocol',
                    'rationale': f'{prob:.0%} risk - standard care'
                })
            
            # Feature-specific interventions
            if 'medication_count_at_discharge' in patient_data.columns:
                if patient['medication_count_at_discharge'] >= 10:
                    recommendations.append({
                        'priority': 'HIGH',
                        'intervention': 'Medication reconciliation with pharmacist',
                        'rationale': f'{patient["medication_count_at_discharge"]} medications - high complexity'
                    })
            
            if 'follow_up_within_7_days_flag' in patient_data.columns:
                if patient['follow_up_within_7_days_flag'] == 0:
                    recommendations.append({
                        'priority': 'HIGH',
                        'intervention': 'Schedule early follow-up appointment',
                        'rationale': 'No follow-up scheduled - strong protective factor'
                    })
            
            if 'comorbidity_index' in patient_data.columns:
                if patient['comorbidity_index'] >= 5:
                    recommendations.append({
                        'priority': 'MODERATE',
                        'intervention': 'Multidisciplinary care team review',
                        'rationale': f'Charlson Index {patient["comorbidity_index"]} - multiple conditions'
                    })
            
            if 'discharge_destination' in patient_data.columns:
                if patient['discharge_destination'] in ['nursing_home', 'rehab']:
                    recommendations.append({
                        'priority': 'MODERATE',
                        'intervention': 'Care transition coordinator',
                        'rationale': 'Discharge to facility - ensure communication'
                    })
            
            interventions.append({'recommendations': recommendations[:5]})  # Top 5
        
        return interventions
    
    def _clean_feature_name(self, feature: str) -> str:
        """Clean up feature names for readability"""
        # Remove prefixes from one-hot encoding
        feature = feature.replace('num__', '').replace('cat__', '')
        
        # Convert to readable format
        readable_names = {
            'age': 'Patient Age',
            'comorbidity_index': 'Comorbidity Burden',
            'medication_count_at_discharge': 'Medication Complexity',
            'previous_admissions_12m': 'Previous Admissions',
            'length_of_stay_days': 'Length of Stay',
            'follow_up_within_7_days_flag': 'Early Follow-up Scheduled',
            'hemoglobin': 'Hemoglobin Level',
            'icu_stay_flag': 'ICU Stay',
            'prior_30_day_readmission_flag': 'Recent Readmission',
            'insurance_type_Medicare': 'Medicare Insurance',
            'insurance_type_Self-pay': 'Self-Pay Status'
        }
        
        return readable_names.get(feature, feature.replace('_', ' ').title())
    
    def _create_risk_profile(self, patient: pd.Series) -> Dict:
        """Create comprehensive risk profile"""
        profile = {}
        
        # Utilization history
        if 'previous_admissions_12m' in patient.index:
            if patient['previous_admissions_12m'] >= 3:
                profile['Previous Utilization'] = 'HIGH'
            elif patient['previous_admissions_12m'] >= 1:
                profile['Previous Utilization'] = 'MEDIUM'
            else:
                profile['Previous Utilization'] = 'LOW'
        
        # Comorbidity burden
        if 'comorbidity_index' in patient.index:
            if patient['comorbidity_index'] >= 5:
                profile['Comorbidity Burden'] = 'HIGH'
            elif patient['comorbidity_index'] >= 3:
                profile['Comorbidity Burden'] = 'MEDIUM'
            else:
                profile['Comorbidity Burden'] = 'LOW'
        
        # Medication complexity
        if 'medication_count_at_discharge' in patient.index:
            if patient['medication_count_at_discharge'] >= 10:
                profile['Medication Complexity'] = 'HIGH'
            elif patient['medication_count_at_discharge'] >= 5:
                profile['Medication Complexity'] = 'MEDIUM'
            else:
                profile['Medication Complexity'] = 'LOW'
        
        # Recent hospitalization
        if 'prior_30_day_readmission_flag' in patient.index:
            profile['Recent Hospitalization'] = 'HIGH' if patient['prior_30_day_readmission_flag'] == 1 else 'LOW'
        
        # Age/demographics
        if 'age' in patient.index:
            if patient['age'] >= 75:
                profile['Demographics Risk'] = 'HIGH'
            elif patient['age'] >= 65:
                profile['Demographics Risk'] = 'MEDIUM'
            else:
                profile['Demographics Risk'] = 'LOW'
        
        return profile
    
    def print_patient_report(self, results: Dict, patient_index: int = 0):
        """
        Print comprehensive patient report
        """
        if results is None:
            print("❌ No results to display (validation failed)")
            return
        
        print("\n" + "="*80)
        print(f"COMPREHENSIVE READMISSION RISK REPORT - PATIENT {patient_index + 1}")
        print("="*80 + "\n")
        
        # Layer 1: Binary prediction
        layer1 = results['layer1_prediction'].iloc[patient_index]
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ LAYER 1: WILL THE PATIENT BE READMITTED?                                   │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        print(f"  Prediction: {layer1['will_readmit']}")
        print(f"  Probability: {layer1['probability']:.1%}")
        print(f"  Confidence: {layer1['confidence']}")
        print()
        
        # Layer 2: Risk level
        layer2 = results['layer2_risk_level'].iloc[patient_index]
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ LAYER 2: HOW LIKELY IS READMISSION?                                        │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        print(f"  Risk Tier: {layer2['risk_tier']}")
        print(f"  Risk Level: {layer2['probability_range']}")
        print(f"  Urgency: {layer2['urgency']}")
        print()
        
        # Layer 3: Explanation
        layer3 = results['layer3_why'][patient_index]
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ LAYER 3: WHY IS THIS PATIENT AT RISK?                                      │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        
        print("\n  PRIMARY RISK FACTORS:")
        for i, factor in enumerate(layer3['risk_factors'], 1):
            print(f"    {i}. {factor['feature']}")
            print(f"       Impact: {factor['impact']} (contribution: {factor['contribution']:.3f})")
        
        if layer3['protective_factors']:
            print("\n  PROTECTIVE FACTORS:")
            for i, factor in enumerate(layer3['protective_factors'], 1):
                print(f"    {i}. {factor['feature']}")
                print(f"       Impact: {factor['impact']} (contribution: {factor['contribution']:.3f})")
        
        print("\n  RISK PROFILE:")
        for category, level in layer3['risk_profile'].items():
            symbol = "⬆️" if level == "HIGH" else "➡️" if level == "MEDIUM" else "⬇️"
            print(f"    {symbol} {category:<30} {level}")
        print()
        
        # Layer 4: Time prediction
        layer4 = results['layer4_when'].iloc[patient_index]
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ LAYER 4: WHEN IS READMISSION MOST LIKELY?                                  │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        print(f"  7-day risk:  {layer4['7_day_risk']:.1%}")
        print(f"  30-day risk: {layer4['30_day_risk']:.1%}")
        print(f"  90-day risk: {layer4['90_day_risk']:.1%}")
        print(f"\n  Most likely window: {layer4['most_likely_window']}")
        print(f"  Note: {layer4['note']}")
        print()
        
        # Layer 5: Interventions
        layer5 = results['layer5_intervention'][patient_index]
        print("┌─────────────────────────────────────────────────────────────────────────────┐")
        print("│ LAYER 5: WHAT INTERVENTION SHOULD BE CONSIDERED?                           │")
        print("└─────────────────────────────────────────────────────────────────────────────┘")
        for i, rec in enumerate(layer5['recommendations'], 1):
            priority_symbol = "🔴" if rec['priority'] == "URGENT" else "🟠" if rec['priority'] == "HIGH" else "🟡" if rec['priority'] == "MODERATE" else "🟢"
            print(f"  {priority_symbol} [{rec['priority']}] {rec['intervention']}")
            print(f"      Rationale: {rec['rationale']}")
            if i < len(layer5['recommendations']):
                print()
        
        print()
        print("="*80)
        print("END OF REPORT")
        print("="*80 + "\n")


# ============================================================================
# COMMAND-LINE DEMO
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE READMISSION PREDICTION SYSTEM - DEMO")
    print("="*80 + "\n")
    
    # Load sample data
    df = pd.read_csv("patient_data_final.csv")
    
    # Get one high-risk and one low-risk patient
    sample_data = df.drop(columns=['patient_id', 'readmitted_30_days', 'drg_code']).iloc[[100, 500]]
    
    # Initialize system
    system = ComprehensiveReadmissionSystem()
    
    # Make predictions
    print("Making comprehensive predictions for 2 sample patients...\n")
    results = system.predict(sample_data)
    
    # Print reports
    print("\n" + "#"*80)
    print("# PATIENT 1 REPORT")
    print("#"*80)
    system.print_patient_report(results, patient_index=0)
    
    print("\n" + "#"*80)
    print("# PATIENT 2 REPORT")
    print("#"*80)
    system.print_patient_report(results, patient_index=1)
    
    print("\n✓ Demo complete!")
    print("Use system.predict(patient_data) for batch predictions")
    print()
