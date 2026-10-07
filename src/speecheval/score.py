"""Pure delivery rubric using decimal half-up rounding, not perceptual ground truth."""
from decimal import Decimal, ROUND_HALF_UP


def rubric_scores(regions: list[dict], duration_s: float | Decimal, config: dict) -> dict[str,float]:
    """Score regions in seconds against first-word to last-word speech duration."""
    duration=Decimal(str(duration_s))
    if not duration.is_finite() or duration<=0:raise ValueError('Speech duration must be positive')
    weights={key:Decimal(str(value)) for key,value in config['weights'].items()}
    if (set(weights)!=set(config['categories']) or any(not value.is_finite() or value<0 for value in weights.values())
            or sum(weights.values())!=1):raise ValueError('Rubric weights must be finite, nonnegative, cover categories, and sum to one')
    values={}
    for category,spec in config['categories'].items():
        penalty=Decimal(0)
        for region in regions:
            if region['type'] not in spec['types']:continue
            severity=Decimal(str(region['severity']))
            if severity not in (1,2,3,4,5):raise ValueError('Severity must be an integer from one to five')
            if spec['kind']=='event':penalty+=severity*Decimal(str(config['event_penalty']))
            else:
                span=Decimal(str(region['end']))-Decimal(str(region['start']))
                if span<0:raise ValueError('Region end precedes start')
                penalty+=severity*span/duration*Decimal(str(config['duration_weight']))
        values[category]=max(Decimal(0),min(Decimal(10),Decimal(10)-penalty)).quantize(Decimal('.1'),rounding=ROUND_HALF_UP)
    values['overall']=sum(weights[key]*values[key] for key in weights).quantize(Decimal('.1'),rounding=ROUND_HALF_UP)
    return {key:float(value) for key,value in values.items()}
