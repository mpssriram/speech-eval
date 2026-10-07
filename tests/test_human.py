"""Imported human annotations remain distinct from intended instructions."""
import pytest
from speecheval import human as h


def alignment():
    return {'recording_id':'sample__user__take02','duration_s':2.,'words':[
        {'i':0,'start':.2,'end':.5},{'i':1,'start':1.,'end':1.3},{'i':2,'start':1.3,'end':1.8}]}


def test_labels_import_maps_actual_regions_and_gap_events():
    result=h.annotation_labels(alignment(),[(.2,1.8,'rushing:3'),(.5,1.,'awkward_pause:2')])
    assert result['source']=='human' and result['reference_id'] is None
    assert result['flaws'][0]['word_start']==0 and result['flaws'][0]['word_end']==2
    assert result['flaws'][1]['word_start']==0 and result['flaws'][1]['word_end']==1


def test_labels_import_rejects_unknown_types_invalid_severity_and_outside_audio():
    for item in [(.2,.5,'rushing:0'),(.2,.5,'fake:2'),(1.9,2.1,'mumbling:3')]:
        with pytest.raises(ValueError):h.annotation_labels(alignment(),[item])


def test_annotation_empty_tier_stays_empty_not_inferred_from_intentions():
    assert h.annotation_labels(alignment(),[])['flaws']==[]
