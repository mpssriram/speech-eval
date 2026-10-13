"""Isolated post-hoc pause sensitivity; the primary v1 scoring path never imports this module."""
from __future__ import annotations
from copy import deepcopy
import math
from speecheval.detect import z_table
from speecheval.reference import inverse, transform


def floor_reference(reference: dict, settings: dict | None = None) -> dict:
    """Return an experimental reference with pause sigma floored in natural-log units.

    The optional ``pause_sigma_floor_s`` setting is in seconds, defaults OFF, and
    does not mutate the retained reference or change any non-pause summary.
    """
    floor=(settings or {}).get('pause_sigma_floor_s')
    if floor is None or floor==0 and not isinstance(floor,bool):return reference
    if isinstance(floor,bool) or not isinstance(floor,(int,float)) or not math.isfinite(floor) or floor<0:
        raise ValueError('pause_sigma_floor_s must be a finite nonnegative number of seconds, or null')
    adjusted=deepcopy(reference)
    for summaries in adjusted['features'].values():
        pause=summaries.get('pause')
        if pause is None:continue
        centre=inverse('pause',pause['mu'])
        transformed_floor=transform('pause',centre+floor)-transform('pause',centre)
        pause['sigma']=max(pause['sigma'],transformed_floor)
    return adjusted


def floor_z_table(alignment: dict, values: list[dict], reference: dict,
                  mapping: list[int | None], settings: dict | None = None) -> list[dict]:
    """Use v1's exact mapping, masking and four-significant-digit z rounding.

    Missing/disabled floor yields the unchanged v1 evidence table. ON modifies
    pause denominators only; all region and matching rules remain external v1 code.
    """
    return z_table(alignment,values,floor_reference(reference,settings),mapping)
