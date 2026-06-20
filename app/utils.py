import hashlib

def make_fingerprint(signal: dict) -> str:
    keys = ["asset", "side", "entry", "stop_loss", "take_profit", "timeframe", "htf_context"]
    txt = "|".join(str(signal.get(k, "")) for k in keys)
    return hashlib.sha256(txt.encode()).hexdigest()

def calc_rr(entry: float, stop: float, tp: float, side: str) -> float:
    if side.upper() == "BUY":
        risk = max(1e-8, entry - stop)
        reward = abs(tp - entry)
    else:
        risk = max(1e-8, stop - entry)
        reward = abs(entry - tp)
    return round(reward / risk, 2)
