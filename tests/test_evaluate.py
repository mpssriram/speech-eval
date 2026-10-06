"""Independent boundary labels, numeric word remapping, and bake-off arithmetic."""
import pytest
import json
from speecheval import evaluate
from speecheval.transcripts import normalize_tokens


def test_dataset_validation_rejects_stale_provenance_and_wrong_aligner(tmp_path):
    from speecheval.verify import _hash_bytes
    record={'recording_id':'sample','body':'one two','uncertain':[0]}
    identities={'sample':_hash_bytes(json.dumps(record,sort_keys=True).encode())}
    config={'alignment':{'mfa':{'beam':100}}}
    for name in ('mfa','whisperx'):
        directory=tmp_path/'data/alignment'/name;directory.mkdir(parents=True)
        payload={'schema':'alignment/v1','recording_id':'sample','aligner':{'name':name},
                 'audio':'audio.wav','transcript':'text.txt','duration_s':2.,'sentences':[],
                 'warnings':[],'uncertain_words':[0],'words':[
                     {'i':0,'text':'one','norm':'one','sentence':0,'start':0.,'end':.5},
                     {'i':1,'text':'two','norm':'two','sentence':0,'start':.6,'end':1.}]}
        directory.joinpath('sample.json').write_text(json.dumps(payload))
        settings={'beam':100} if name=='mfa' else {'threads':1,'model':'WAV2VEC2_ASR_BASE_960H'}
        directory.joinpath('provenance.json').write_text(json.dumps({'input_hashes':identities,'settings':settings}))
    evaluate.validate_dataset(tmp_path,config,[record])
    path=tmp_path/'data/alignment/whisperx/sample.json'
    payload=json.loads(path.read_text());payload['aligner']['name']='mfa';path.write_text(json.dumps(payload))
    with pytest.raises(ValueError,match='identity'):
        evaluate.validate_dataset(tmp_path,config,[record])
    payload['aligner']['name']='whisperx';path.write_text(json.dumps(payload))
    with pytest.raises(ValueError,match='provenance'):
        evaluate.validate_dataset(tmp_path,config,[dict(record,body='changed')])


def test_gold_index_mapping_requires_complete_current_migration(tmp_path):
    from speecheval.verify import _hash_bytes
    archive=tmp_path/'data/review/before_number_expansion/transcripts';archive.mkdir(parents=True)
    current=tmp_path/'data/transcripts/as_spoken';current.mkdir(parents=True)
    archive.joinpath('sample.txt').write_text('10,000 cars')
    current.joinpath('sample.txt').write_text('ten thousand cars')
    selection={'recordings':{'sample':{'items':[{'word_index':1,'text':'cars'}]}}}
    record={'input_sha256':_hash_bytes(archive.joinpath('sample.txt').read_bytes()),
            'output_sha256':_hash_bytes(current.joinpath('sample.txt').read_bytes()),'old_to_new':{'0':[0,1],'1':[2]}}
    result=evaluate.validate_migration(tmp_path,selection,{'recordings':{'sample':record}})
    assert result['sample'][1]==[2]
    with pytest.raises(ValueError,match='migration'):
        evaluate.validate_migration(tmp_path,selection,{'recordings':{}})
    record['old_to_new'].pop('1')
    with pytest.raises(ValueError,match='mapping'):
        evaluate.validate_migration(tmp_path,selection,{'recordings':{'sample':record}})


def test_model_fingerprint_changes_when_checkpoint_or_software_changes(tmp_path):
    checkpoint=tmp_path/'model.pth';checkpoint.write_bytes(b'weights1')
    first=evaluate.inference_fingerprint({'model':checkpoint},{'torch':'1'})
    checkpoint.write_bytes(b'weights2')
    assert first!=evaluate.inference_fingerprint({'model':checkpoint},{'torch':'1'})
    assert first!=evaluate.inference_fingerprint({'model':checkpoint},{'torch':'2'})


def test_number_word_hyphens_match_digits_without_changing_compound_normalization():
    assert normalize_tokens('35 thirty-five C-1 C-one')==['thirty','five','thirty','five','c','one','c','one']
    assert normalize_tokens('well-being')==['wellbeing']


def test_blank_intervals_ignored_and_question_labels_excluded():
    boxes=[{'word_index':0,'text':'one','start':0.,'end':.5},
           {'word_index':2,'text':'three','start':1.,'end':1.5}]
    intervals=[(0.,.1,''),(.1,.4,'one'),(.4,1.1,''),(1.1,1.4,'three?'),(1.4,2.,'')]
    result=evaluate.validate_gold_intervals(intervals,boxes,2.)
    assert len(result['scored'])==1 and result['excluded_question']==1
    assert result['labelled']==2 and result['total_intervals']==5


def test_gold_rejects_mismatched_labels_and_out_of_audio_bounds():
    boxes=[{'word_index':0,'text':'one','start':0.,'end':.5}]
    with pytest.raises(ValueError,match='label'):
        evaluate.validate_gold_intervals([(0.,.3,'two')],boxes,1.)
    with pytest.raises(ValueError,match='bounds'):
        evaluate.validate_gold_intervals([(.9,1.2,'one')],boxes,1.)


def test_gold_flags_but_does_not_clip_independent_boundary_outside_old_box():
    boxes=[{'word_index':0,'text':'35','start':0.,'end':.6}]
    result=evaluate.validate_gold_intervals([(.2,1.1,'35')],boxes,2.)
    assert result['outside_template']==1
    assert result['scored'][0]['end']==1.1


def test_number_expansion_preserves_punctuation_and_maps_old_word_indices():
    text='# header: 2026\nWe saw 35 and 10,000 cars, in 24 hours. C-1.\n'
    expanded,mapping=evaluate.expand_numbers(text)
    assert expanded=='# header: 2026\nWe saw thirty-five and ten thousand cars, in twenty-four hours. C-one.\n'
    assert mapping[2]==[2] and mapping[4]==[4,5] and mapping[5]==[6]


def test_number_expansion_compares_old_gold_number_to_all_new_words():
    words=[{'i':0,'text':'ten','start':.2,'end':.5},{'i':1,'text':'thousand','start':.5,'end':1.}]
    assert evaluate.mapped_boundary(words,[0,1])==(.2,1.)


def test_error_metrics_in_ms_and_inclusive_thresholds():
    metrics=evaluate.error_metrics([.010,.020,.050,.100])
    assert metrics['median_ms']==35.
    assert metrics['mean_ms']==45.
    assert metrics['within_20_ms_pct']==50.
    assert metrics['within_50_ms_pct']==75.


def test_spec_recommendation_uses_combined_median_then_cpu_determinism():
    evidence={'mfa':{'overall':{'median_ms':30},'deterministic':True,'device':'cpu'},
              'whisperx':{'overall':{'median_ms':25},'deterministic':True,'device':'cpu'}}
    assert evaluate.recommend_aligner(evidence)=='mfa'
    evidence['whisperx']['overall']['median_ms']=15
    assert evaluate.recommend_aligner(evidence)=='whisperx'
