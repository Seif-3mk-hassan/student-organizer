"""Central GPA math — pure, testable, single source."""
from typing import Sequence

def _grade_point(score: float, max_score: float) -> float:
    if max_score <= 0:
        return 0.0
    pct = score / max_score
    if pct >= 0.9: return 4.0
    if pct >= 0.8: return 3.0
    if pct >= 0.7: return 2.0
    if pct >= 0.6: return 1.0
    return 0.0

def compute_gpa(grades: Sequence[dict]) -> float:
    """grades: list of dicts with weight, score, max_score. Normalizes weights."""
    if not grades:
        return 0.0
    total_w = sum(g["weight"] for g in grades)
    if total_w == 0:
        return 0.0
    pts = 0.0
    for g in grades:
        gp = _grade_point(g["score"], g["max_score"])
        # normalize weight
        pts += gp * (g["weight"] / total_w)
    return round(pts, 2)

def what_if_final(current: Sequence[dict], final_weight: float, target_gpa: float) -> float | None:
    """What score needed on final (max 100) to reach target. None if impossible."""
    if final_weight <= 0 or final_weight >= 100:
        return None
    # brute search 0..100
    for s in range(101):
        cand = list(current) + [{"weight": final_weight, "score": float(s), "max_score": 100}]
        if compute_gpa(cand) >= target_gpa:
            return float(s)
    return None
