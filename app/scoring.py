from typing import Dict

def score_evidence(evidence: Dict) -> Dict:
    score = 0
    reasons = []

    if evidence.get("htf_alignment"):
        score += 20
        reasons.append("HTF Alignment")

    if evidence.get("liquidity_sweep"):
        score += 15
        reasons.append("Liquidity Sweep")

    if evidence.get("order_block"):
        score += 15
        reasons.append("Order Block")

    if evidence.get("fvg"):
        score += 10
        reasons.append("Fair Value Gap")

    if evidence.get("mss"):
        score += 15
        reasons.append("MSS Confirmation")

    if evidence.get("cvd"):
        score += 10
        reasons.append("CVD Confirmation")

    if evidence.get("oi_confirmation"):
        score += 10
        reasons.append("Open Interest Confirmation")

    rr = evidence.get("rr", 0)
    if rr > 3:
        score += 5
        reasons.append("RR>3")

    confidence = max(0, min(100, int(score)))
    quality = "Reject"
    if confidence < 50:
        quality = "Reject"
    elif 50 <= confidence < 70:
        quality = "Weak"
    elif 70 <= confidence < 85:
        quality = "Good"
    else:
        quality = "A+"

    return {"score": score, "confidence": confidence, "quality": quality, "reasons": reasons}
