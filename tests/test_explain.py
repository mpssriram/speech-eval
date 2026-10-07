from speecheval import explain as e


def test_template_has_exact_measurement_ratio_z_and_quote():
    region={'type':'rushing','start':1.23,'end':3.45,'word_start':0,'word_end':2,
            'evidence':{'participant':6.,'reference':3.,'z':3.},'tags':[]}
    assert e.explanation(region,['four','score','years'])=='1.2–3.5 s, "four score years": you spoke at 6 syllables/s; good readers average 3 (2× faster, 3 SD above). Rushing this phrase reduces its weight.'
    assert 'your previous take' in e.explanation(region,['four','score','years'],mode='B')
