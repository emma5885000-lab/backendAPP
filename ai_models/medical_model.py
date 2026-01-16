"""
MODÈLE IA DE CLASSIFICATION MÉDICALE
Utilise Random Forest pour classifier l'état de santé basé sur les paramètres physiologiques
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

FEATURES = ['cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature']
TARGET = 'status'

CLASS_NAMES = {
    0: 'Sain',
    1: 'Infection légère',
    2: 'Infection modérée',
    3: 'Hypoxie sévère'
}

MODEL_PATH = 'medical_model.pkl'
SCALER_PATH = 'medical_scaler.pkl'


class MedicalClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def load_data(self, filepath='medical_training_data.csv'):
        print(f"📂 Chargement des données: {filepath}")
        df = pd.read_csv(filepath)
        X = df[FEATURES].values
        y = df[TARGET].values
        print(f"✅ {len(df)} échantillons chargés")
        return X, y
    
    def train(self, X, y, test_size=0.2):
        print("\n🔄 Entraînement du modèle...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Entraînement terminé!")
        print(f"📊 Précision: {accuracy*100:.2f}%")
        print("\n📋 Rapport:")
        print(classification_report(y_test, y_pred, target_names=[CLASS_NAMES[i] for i in sorted(CLASS_NAMES.keys())]))
        
        print("\n🔍 Importance des paramètres:")
        for feat, imp in sorted(zip(FEATURES, self.model.feature_importances_), key=lambda x: x[1], reverse=True):
            print(f"   • {feat}: {imp*100:.1f}%")
        
        return accuracy
    
    def save(self, model_path=MODEL_PATH, scaler_path=SCALER_PATH):
        if not self.is_trained:
            raise Exception("Le modèle n'est pas encore entraîné!")
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        print(f"\n💾 Modèle sauvegardé: {model_path}")
        print(f"💾 Scaler sauvegardé: {scaler_path}")
    
    def load(self, model_path=MODEL_PATH, scaler_path=SCALER_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modèle non trouvé: {model_path}")
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.is_trained = True
        print(f"✅ Modèle chargé: {model_path}")
    
    def predict(self, cov_ppb, eco2_ppm, heart_rate, spo2, temperature):
        """
        Prédit l'état de santé à partir des paramètres
        
        Returns: dict avec status, status_name, confidence, probabilities
        """
        if not self.is_trained:
            raise Exception("Le modèle n'est pas chargé!")
        
        X = np.array([[cov_ppb, eco2_ppm, heart_rate, spo2, temperature]])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        confidence = probabilities[prediction] * 100
        
        return {
            'status': int(prediction),
            'status_name': CLASS_NAMES[prediction],
            'confidence': round(confidence, 2),
            'probabilities': {CLASS_NAMES[i]: round(p*100, 2) for i, p in enumerate(probabilities)}
        }


# ============================================
# FONCTION DE PRÉDICTION SIMPLE
# ============================================

_classifier = None

def get_classifier():
    global _classifier
    if _classifier is None:
        _classifier = MedicalClassifier()
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, MODEL_PATH)
        scaler_path = os.path.join(script_dir, SCALER_PATH)
        _classifier.load(model_path, scaler_path)
    return _classifier


def predict_health_status(cov_ppb, eco2_ppm, heart_rate, spo2, temperature):
    """
    Fonction simple pour prédire l'état de santé
    
    Exemple:
        result = predict_health_status(400, 420, 75, 98, 36.8)
        print(result['status_name'])  # 'Sain'
    """
    classifier = get_classifier()
    return classifier.predict(cov_ppb, eco2_ppm, heart_rate, spo2, temperature)


# ============================================
# ENTRAÎNEMENT
# ============================================

if __name__ == "__main__":
    print("=" * 60)
    print("ENTRAÎNEMENT DU MODÈLE DE CLASSIFICATION MÉDICALE")
    print("=" * 60)
    
    classifier = MedicalClassifier()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, 'medical_training_data.csv')
    
    X, y = classifier.load_data(data_path)
    classifier.train(X, y)
    
    model_path = os.path.join(script_dir, MODEL_PATH)
    scaler_path = os.path.join(script_dir, SCALER_PATH)
    classifier.save(model_path, scaler_path)
    
    print("\n" + "=" * 60)
    print("TEST DE PRÉDICTION")
    print("=" * 60)
    
    test_cases = [
        (400, 420, 75, 98, 36.8),   # Sain
        (750, 500, 95, 95, 37.8),   # Infection légère
        (900, 580, 110, 91, 38.5), # Infection modérée
        (1000, 650, 125, 82, 39.2) # Hypoxie sévère
    ]
    
    for cov, eco2, hr, spo2, temp in test_cases:
        result = classifier.predict(cov, eco2, hr, spo2, temp)
        print(f"\nEntrée: COV={cov}, eCO2={eco2}, HR={hr}, SpO2={spo2}, T={temp}")
        print(f"Résultat: {result['status_name']} (confiance: {result['confidence']:.1f}%)")
    
    print("\n" + "=" * 60)
    print("✅ Modèle prêt à l'emploi!")
    print("=" * 60)
