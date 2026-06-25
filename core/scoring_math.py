# core\scoring_math.py

from scipy.stats import norm

def compute_z_score(raw, m, sigma):
    """
    z = (raw - m) / sigma
    """

    if sigma == 0:
        return None
    '''
    print("\n--- Z SCORE ---")
    print("raw:", raw, "m:", m, "sigma:", sigma)
    '''
    return round((raw - m) / sigma, 2)

def z_to_percentile(z):
    """
    Convertit un z-score en percentile (0-100)
    """
    if z is None:
        return None

    return round(norm.cdf(z) * 100, 1)

def interpret_percentile(p):
    if p is None:
        return None
    if p >= 97:
        return "très atypique"
    if p >= 90:
        return "atypique"
    if p >= 25:
        return "dans la norme"
    if p >= 10:
        return "fragilité"
    return "difficulté marquée"