"""Plotting payloads in physical feature units, with participant word timing."""
from __future__ import annotations
from pathlib import Path
import math
import numpy as np
import pandas as pd
from fastapi import HTTPException
from speecheval.reference import recording_values, build_reference, map_words, inverse


def analysis_tracks(root: Path, result: dict) -> dict:
    """Return five per-word curves and 20 ms frames; null means unavailable evidence."""
    alignment, values = recording_values(root, result['recording_id'])
    reference = None
    if result['mode'] != 'C':
        reference = build_reference(result['text_id'], result['reference'].get('exclude_speaker'), root,
                                    result['reference'].get('baseline_recording_id') if result['mode'] == 'B' else None)
        if reference['reference_version'] != result['reference']['reference_version']:
            raise HTTPException(409, 'Reference changed since this analysis; create a new analysis for matching tracks')
    mapping = map_words([w['norm'] for w in alignment['words']], reference['words']) if reference else [None] * len(values)
    def finite(value):
        return float(value) if value is not None and math.isfinite(value) else None
    words = []
    for word, row, mapped in zip(alignment['words'], values, mapping):
        bands = {}
        if mapped is not None:
            for feature, distribution in reference['features'][str(mapped)].items():
                if distribution:
                    mu, sigma = distribution['mu'], distribution['sigma']
                    bands[feature] = {'mu': finite(inverse(feature, mu)), 'sigma_transformed': sigma,
                                      'low': finite(inverse(feature, mu - 2 * sigma)), 'high': finite(inverse(feature, mu + 2 * sigma))}
        words.append({**word, 'features': {f: finite(inverse(f, v)) for f, v in row.items()}, 'reference': bands})
    frames = pd.read_parquet(root / 'data/features/frames' / f"{result['recording_id']}.parquet")
    # Frames are 10 ms; select one sample per 20 ms bin rather than averaging dB.
    sampled = frames.iloc[::2]
    return {'words': words, 'frames': {('time_s' if name == 't' else name): [finite(v) for v in sampled[name]]
                                      for name in ('t', 'f0_st', 'int_rel_db') if name in sampled.columns},
            'frame_step_s': .02}
