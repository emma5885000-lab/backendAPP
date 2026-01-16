"""
Service d'intégration du modèle IA médical pour le backend Django
"""

import numpy as np
import os
import joblib

FEATURES = ['cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature']

CLASS_NAMES = {
    0: 'Sain',
    1: 'Infection légère',
    2: 'Infection modérée',
    3: 'Hypoxie sévère'
}

# Chemin vers les fichiers du modèle (dans le dossier ai_models du backend)
AI_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '..', 'ai_models'
)
MODEL_PATH = os.path.join(AI_MODEL_DIR, 'medical_model.pkl')
SCALER_PATH = os.path.join(AI_MODEL_DIR, 'medical_scaler.pkl')


class MedicalAIService:
    """Service singleton pour les prédictions IA médicales"""
    
    _instance = None
    _model = None
    _scaler = None
    _is_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Charge le modèle et le scaler"""
        if self._is_loaded:
            return True
        
        try:
            if not os.path.exists(MODEL_PATH):
                print(f"⚠️ Modèle non trouvé: {MODEL_PATH}")
                return False
            
            self._model = joblib.load(MODEL_PATH)
            self._scaler = joblib.load(SCALER_PATH)
            self._is_loaded = True
            print(f"✅ Modèle IA chargé depuis: {MODEL_PATH}")
            return True
        except Exception as e:
            print(f"❌ Erreur chargement modèle: {e}")
            return False
    
    def predict(self, cov_ppb, eco2_ppm, heart_rate, spo2, temperature):
        """
        Prédit l'état de santé à partir des paramètres du capteur
        
        Args:
            cov_ppb: COV en ppb
            eco2_ppm: eCO2 en ppm
            heart_rate: Fréquence cardiaque
            spo2: Saturation en oxygène
            temperature: Température corporelle
            
        Returns:
            dict avec status, status_name, confidence, probabilities
        """
        if not self._is_loaded:
            if not self.load_model():
                return {
                    'status': -1,
                    'status_name': 'Erreur',
                    'confidence': 0,
                    'probabilities': {},
                    'error': 'Modèle IA non disponible'
                }
        
        try:
            X = np.array([[cov_ppb, eco2_ppm, heart_rate, spo2, temperature]])
            X_scaled = self._scaler.transform(X)
            
            prediction = self._model.predict(X_scaled)[0]
            probabilities = self._model.predict_proba(X_scaled)[0]
            confidence = probabilities[prediction] * 100
            
            return {
                'status': int(prediction),
                'status_name': CLASS_NAMES[prediction],
                'confidence': round(confidence, 2),
                'probabilities': {CLASS_NAMES[i]: round(p*100, 2) for i, p in enumerate(probabilities)}
            }
        except Exception as e:
            return {
                'status': -1,
                'status_name': 'Erreur',
                'confidence': 0,
                'probabilities': {},
                'error': str(e)
            }


# Instance globale du service
ai_service = MedicalAIService()


def predict_health_status(cov_ppb, eco2_ppm, heart_rate, spo2, temperature):
    """
    Fonction utilitaire pour prédire l'état de santé
    
    Exemple:
        result = predict_health_status(400, 420, 75, 98, 36.8)
        print(result['status_name'])  # 'Sain'
    """
    return ai_service.predict(cov_ppb, eco2_ppm, heart_rate, spo2, temperature)
