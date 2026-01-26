#calculs mathematiques pour l'AHP (matrice de Saaty)

import numpy as np

class AHPEngine:
    def __init__(self):
        # Indice de cohérence aléatoire (Saaty)
        self.RI = {3: 0.58, 4: 0.90, 5: 1.12}

    def compute_weights(self, matrix):
        """Calcule les poids (vecteur propre) et le ratio de cohérence."""
        n = matrix.shape[0]
        # Normalisation
        column_sums = matrix.sum(axis=0)
        norm_matrix = matrix / column_sums
        weights = norm_matrix.mean(axis=1)
        
        # Calcul de la cohérence (CR)
        lambda_max = np.real(np.linalg.eigvals(matrix).max())
        ci = (lambda_max - n) / (n - 1)
        cr = ci / self.RI.get(n, 1.0)
        
        return weights, cr