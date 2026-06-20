import pandas as pd
from typing import List, Dict, Any, Optional

def find_body_fvg_zones(
    df: pd.DataFrame,
    min_size: float = 0.0,
    min_size_pct: Optional[float] = None,
) -> List[Dict[str, Any]]:
    zones: List[Dict[str, Any]] = []
    if len(df) < 3:
        return zones

    opens = df['open'].values
    closes = df['close'].values

    for i in range(2, len(df)):
        left = i - 2

        left_body_top = max(opens[left], closes[left])
        left_body_bottom = min(opens[left], closes[left])

        right_body_top = max(opens[i], closes[i])
        right_body_bottom = min(opens[i], closes[i])

        if right_body_bottom > left_body_top:
            zone_bottom = float(left_body_top)
            zone_top = float(right_body_bottom)
            size = zone_top - zone_bottom
            mid = (zone_top + zone_bottom) / 2.0
            size_pct = size / mid if mid != 0 else 0.0

            ok_abs = size >= float(min_size or 0.0)
            ok_pct = True if (min_size_pct is None) else (size_pct >= float(min_size_pct))
            if ok_abs and ok_pct:
                zones.append({
                    'type': 'bull',
                    'left_index': left,
                    'right_index': i,
                    'zone_bottom': zone_bottom,
                    'zone_top': zone_top,
                    'size': float(size),
                    'size_pct': float(size_pct),
                    'filled': False,
                    'filled_index': None,
                })
        if right_body_top < left_body_bottom:
            zone_bottom = float(right_body_top)
            zone_top = float(left_body_bottom)
            size = zone_top - zone_bottom
            mid = (zone_top + zone_bottom) / 2.0
            size_pct = size / mid if mid != 0 else 0.0

            ok_abs = size >= float(min_size or 0.0)
            ok_pct = True if (min_size_pct is None) else (size_pct >= float(min_size_pct))
            if ok_abs and ok_pct:
                zones.append({
                    'type': 'bear',
                    'left_index': left,
                    'right_index': i,
                    'zone_bottom': zone_bottom,
                    'zone_top': zone_top,
                    'size': float(size),
                    'size_pct': float(size_pct),
                    'filled': False,
                    'filled_index': None,
                })
    return zones


def mark_fvg_filled(
    df: pd.DataFrame,
    zones: List[Dict[str, Any]],
    use_wicks_for_fill: bool = True,
) -> List[Dict[str, Any]]:
    highs = df['high'].values
    lows = df['low'].values
    opens = df['open'].values
    closes = df['close'].values
    n = len(df)

    for z in zones:
        start = z['right_index'] + 1
        for j in range(start, n):
            if use_wicks_for_fill:
                bar_low = float(lows[j])
                bar_high = float(highs[j])
            else:
                bar_low = float(min(opens[j], closes[j]))
                bar_high = float(max(opens[j], closes[j]))

            if (bar_high >= z['zone_bottom']) and (bar_low <= z['zone_top']):
                z['filled'] = True
                z['filled_index'] = int(j)
                break
    return zones


def get_active_body_fvg_zones(
    df: pd.DataFrame,
    lookback_bars: int = 200,
    min_size: float = 0.0,
    min_size_pct: Optional[float] = None,
    use_wicks_for_fill: bool = True,
) -> List[Dict[str, Any]]:
    if lookback_bars < 3:
        lookback_bars = 3
    df_slice = df.iloc[-lookback_bars:].reset_index(drop=True)
    zones = find_body_fvg_zones(df_slice, min_size=min_size, min_size_pct=min_size_pct)
    zones = mark_fvg_filled(df_slice, zones, use_wicks_for_fill=use_wicks_for_fill)
    offset = len(df) - len(df_slice)
    active = []
    for z in zones:
        if not z['filled']:
            z_copy = z.copy()
            z_copy['left_index'] = int(z_copy['left_index'] + offset)
            z_copy['right_index'] = int(z_copy['right_index'] + offset)
            z_copy['filled_index'] = None
            active.append(z_copy)
    return active
