"""
GÉNÉRATEUR DE DONNÉES RÉALISTES
Basé sur des plages physiologiques médicalement validées
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class MedicalDataGenerator:
    """
    Génère des données synthétiques basées sur des profils médicaux réalistes
    """
    
    def __init__(self, random_seed=42):
        np.random.seed(random_seed)
        
        # Définition des profils médicaux basés sur la littérature
        self.profiles = {
            'sain': {
                'description': 'Personne en bonne santé',
                'cov_ppb': (300, 500, 80),      # (min, max, std)
                'eco2_ppm': (380, 450, 25),
                'heart_rate': (60, 85, 8),
                'spo2': (96, 100, 1.5),
                'temperature': (36.4, 37.2, 0.3),
                'probability': 0.50  # 50% des cas
            },
            'infection_legere': {
                'description': 'Infection respiratoire légère (rhume, grippe)',
                'cov_ppb': (600, 900, 100),
                'eco2_ppm': (450, 550, 40),
                'heart_rate': (85, 105, 12),
                'spo2': (94, 97, 2),
                'temperature': (37.3, 38.5, 0.5),
                'probability': 0.25
            },
            'infection_moderee': {
                'description': 'Infection respiratoire modérée (bronchite, COVID)',
                'cov_ppb': (700, 1100, 120),
                'eco2_ppm': (500, 650, 50),
                'heart_rate': (95, 120, 15),
                'spo2': (89, 94, 2.5),
                'temperature': (37.8, 39.5, 0.6),
                'probability': 0.15
            },
            'hypoxie_severe': {
                'description': 'Détresse respiratoire sévère',
                'cov_ppb': (800, 1200, 130),
                'eco2_ppm': (550, 700, 60),
                'heart_rate': (105, 140, 18),
                'spo2': (75, 89, 4),
                'temperature': (37.5, 40, 0.8),
                'probability': 0.10
            }
        }
        
        # Mapping vers les classes numériques
        self.class_mapping = {
            'sain': 0,
            'infection_legere': 1,
            'infection_moderee': 2,
            'hypoxie_severe': 3
        }
    
    def generate_sample(self, profile_name):
        """Génère un échantillon pour un profil donné"""
        profile = self.profiles[profile_name]
        
        sample = {}
        for param in ['cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature']:
            min_val, max_val, std = profile[param]
            mean_val = (min_val + max_val) / 2
            
            # Distribution normale tronquée
            value = np.random.normal(mean_val, std)
            value = np.clip(value, min_val, max_val)
            
            sample[param] = value
        
        sample['status'] = self.class_mapping[profile_name]
        sample['status_name'] = profile_name
        
        return sample
    
    def add_noise_and_variations(self, df):
        """
        Ajoute du bruit et des variations pour simuler:
        - Erreurs de mesure des capteurs
        - Variations individuelles
        - Conditions environnementales
        """
        # Bruit des capteurs (±5%)
        noise_level = 0.05
        
        df['cov_ppb'] *= np.random.uniform(1-noise_level, 1+noise_level, len(df))
        df['eco2_ppm'] *= np.random.uniform(1-noise_level, 1+noise_level, len(df))
        df['heart_rate'] *= np.random.uniform(1-noise_level/2, 1+noise_level/2, len(df))
        df['spo2'] *= np.random.uniform(1-noise_level/10, 1+noise_level/10, len(df))
        df['temperature'] += np.random.normal(0, 0.1, len(df))
        
        # S'assurer que les valeurs restent réalistes
        df['cov_ppb'] = df['cov_ppb'].clip(100, 2000)
        df['eco2_ppm'] = df['eco2_ppm'].clip(350, 800)
        df['heart_rate'] = df['heart_rate'].clip(40, 180).round(0)
        df['spo2'] = df['spo2'].clip(70, 100).round(1)
        df['temperature'] = df['temperature'].clip(35, 41).round(1)
        
        return df
    
    def add_correlations(self, df):
        """
        Ajoute des corrélations physiologiques réalistes
        Ex: Fièvre augmente la fréquence cardiaque
        """
        # Pour chaque degré au-dessus de 37°C, ajouter ~10 bpm
        temp_effect = (df['temperature'] - 37) * 10
        df['heart_rate'] = df['heart_rate'] + temp_effect.clip(0, 30)
        df['heart_rate'] = df['heart_rate'].clip(40, 180)
        
        # Si SpO2 très bas, augmenter fréquence cardiaque (compensation)
        spo2_effect = (95 - df['spo2']).clip(0, 20) * 2
        df['heart_rate'] = df['heart_rate'] + spo2_effect
        df['heart_rate'] = df['heart_rate'].clip(40, 180)
        
        return df
    
    def generate_dataset(self, n_samples=2000, add_outliers=True):
        """
        Génère un dataset complet
        
        Parameters:
        -----------
        n_samples : int
            Nombre total d'échantillons
        add_outliers : bool
            Ajouter des cas atypiques (5% du dataset)
        """
        samples = []
        
        # Calculer le nombre d'échantillons par classe
        for profile_name, profile in self.profiles.items():
            n_class = int(n_samples * profile['probability'])
            
            for _ in range(n_class):
                sample = self.generate_sample(profile_name)
                samples.append(sample)
        
        df = pd.DataFrame(samples)
        
        # Ajouter du bruit et des corrélations
        df = self.add_noise_and_variations(df)
        df = self.add_correlations(df)
        
        # Ajouter des outliers (cas atypiques)
        if add_outliers:
            n_outliers = int(len(df) * 0.05)
            outlier_indices = np.random.choice(df.index, n_outliers, replace=False)
            
            for idx in outlier_indices:
                # Modifier aléatoirement un paramètre
                param = np.random.choice(['cov_ppb', 'eco2_ppm', 'heart_rate'])
                df.loc[idx, param] *= np.random.uniform(1.3, 1.7)
        
        # Mélanger le dataset
        df = df.sample(frac=1).reset_index(drop=True)
        
        return df
    
    def visualize_dataset(self, df):
        """Visualise la distribution des données"""
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Distribution des Paramètres Physiologiques', fontsize=16)
        
        params = ['cov_ppb', 'eco2_ppm', 'heart_rate', 'spo2', 'temperature']
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        for idx, param in enumerate(params):
            ax = axes[idx // 3, idx % 3]
            
            for status in df['status'].unique():
                subset = df[df['status'] == status]
                ax.hist(subset[param], alpha=0.6, label=f'Classe {status}', bins=30)
            
            ax.set_xlabel(param)
            ax.set_ylabel('Fréquence')
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        # Matrice de corrélation
        ax = axes[1, 2]
        corr = df[params].corr()
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', ax=ax, cbar_kws={'shrink': 0.8})
        ax.set_title('Corrélations')
        
        plt.tight_layout()
        plt.savefig('dataset_visualization.png', dpi=300, bbox_inches='tight')
        print("✅ Visualisation sauvegardée: dataset_visualization.png")
        plt.show()
    
    def save_dataset(self, df, filename='medical_training_data.csv'):
        """Sauvegarde le dataset"""
        df.to_csv(filename, index=False)
        print(f"\n✅ Dataset sauvegardé: {filename}")
        print(f"📊 Taille: {len(df)} échantillons")
        print(f"\n📈 Distribution des classes:")
        print(df['status_name'].value_counts())
        print(f"\n📋 Statistiques descriptives:")
        print(df.describe())


# ============================================
# UTILISATION
# ============================================

if __name__ == "__main__":
    print("=" * 70)
    print("GÉNÉRATEUR DE DONNÉES MÉDICALES RÉALISTES")
    print("=" * 70)
    
    # Créer le générateur
    generator = MedicalDataGenerator(random_seed=42)
    
    # Afficher les profils
    print("\n📋 Profils médicaux disponibles:\n")
    for name, profile in generator.profiles.items():
        print(f"• {name.upper()}: {profile['description']}")
        print(f"  Probabilité: {profile['probability']*100:.0f}%\n")
    
    # Générer le dataset
    print("\n🔄 Génération du dataset...")
    df = generator.generate_dataset(n_samples=2000, add_outliers=True)
    
    # Sauvegarder
    generator.save_dataset(df)
    
    # Visualiser
    print("\n📊 Création des visualisations...")
    generator.visualize_dataset(df)
    
    print("\n" + "=" * 70)
    print("✅ Dataset prêt à être utilisé pour l'entraînement !")
    print("=" * 70)
    print("\nProchaines étapes:")
    print("1. Utiliser 'medical_training_data.csv' pour entraîner votre modèle")
    print("2. Vérifier les visualisations dans 'dataset_visualization.png'")
    print("3. Adapter les profils si nécessaire dans le code")
    print("=" * 70)