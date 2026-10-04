import pytest
import json

from speecheval.align import base


def test_alignment_preserves_frozen_windows_and_rejects_stale_inputs(tmp_path, monkeypatch):
    from speecheval.align import pipeline
    from speecheval.verify import _hash_bytes
    rid='sample';config={'paths':{'transcripts_as_spoken':'transcripts','alignment':'alignment'},
                         'alignment':{'sentence_window_padding_s':.3}}
    (tmp_path/'transcripts').mkdir();(tmp_path/'alignment/asr').mkdir(parents=True)
    (tmp_path/'alignment/windows').mkdir()
    text=tmp_path/'transcripts/sample.txt';text.write_text('one two')
    asr=tmp_path/'alignment/asr/sample.json';asr.write_text('{}')
    window=tmp_path/'alignment/windows/sample.json'
    payload={'transcript_sha256':_hash_bytes(text.read_bytes()),'source_asr_sha256':_hash_bytes(asr.read_bytes()),
             'cut_start_s':1.,'cut_end_s':3.,'sentences':[{'start':.123,'end':1.8}]}
    window.write_text(json.dumps(payload));before=window.read_bytes()
    monkeypatch.setattr(pipeline,'_refresh_output_windows',lambda *args: pytest.fail('Frozen windows rewritten'))
    rows=[{'recording_id':rid,'cut_start_s':'1','cut_end_s':'3'}]
    pipeline.ensure_windows(tmp_path,config,rows,False)
    assert window.read_bytes()==before
    text.write_text('changed')
    with pytest.raises(ValueError,match='Stale frozen'):
        pipeline.ensure_windows(tmp_path,config,rows,False)
    text.write_text('one two');config['alignment']['sentence_window_padding_s']=.4
    with pytest.raises(ValueError,match='Stale frozen'):
        pipeline.ensure_windows(tmp_path,config,rows,False)


def test_mfa_replaces_stale_owned_audio_link(tmp_path):
    from speecheval.align import mfa
    source=tmp_path/'prepared.wav';target=tmp_path/'corpus.wav'
    source.write_bytes(b'old');mfa.link_audio(source,target)
    replacement=tmp_path/'replacement.wav';replacement.write_bytes(b'new');replacement.replace(source)
    mfa.link_audio(source,target)
    assert target.read_bytes()==b'new'
    assert source.samefile(target)


def test_split_hyphen_and_number_map_to_single_transcript_word():
    assert hasattr(base, 'map_words')
    words, warnings = base.map_words('well-being 12 gone', [
        {'word':'well', 'start':.1,'end':.2}, {'word':'being','start':.2,'end':.3},
        {'word':'twelve','start':.4,'end':.6}, {'word':'gone','start':.8,'end':1.}], 1.2)
    assert len(words)==3
    assert words[0]['start']==.1 and words[0]['end']==.3
    assert words[1]['norm']=='twelve'
    assert not warnings


def test_missing_word_interpolates_and_overlaps_fixed():
    words, warnings = base.map_words('one two three', [
        {'word':'one','start':.1,'end':.4}, {'word':'three','start':.8,'end':1.}], 1.2)
    assert words[1]['start']==.4 and words[1]['end']==.8
    assert warnings==[{'type':'interpolated','word':1}]
    assert all(a['end']<=b['start'] for a,b in zip(words,words[1:]))


def test_alignment_validation_rejects_missing_field_and_bad_uncertain_index():
    assert hasattr(base,'Alignment')
    with pytest.raises(ValueError):
        base.Alignment.model_validate({'schema':'alignment/v1'})


def test_overlap_chain_never_moves_previous_start_backwards():
    words,_=base.map_words('one two three', [
        {'word':'one','start':1.,'end':2.}, {'word':'two','start':.1,'end':.2},
        {'word':'three','start':.3,'end':.4}], 3.)
    assert words[0]['start']==1.
    assert all(a['end']<=b['start'] for a,b in zip(words,words[1:]))


def test_uncertain_indices_validated_and_textgrid_roundtrip(tmp_path):
    from praatio import textgrid
    windows=[{'i':0,'char_start':0,'char_end':13,'text':'one two three','start':0.,'end':1.2,'valid':True}]
    payload=base.make_alignment('synthetic__reader__orig','one two three',windows,[
        {'word':'one','start':.1004,'end':.4},{'word':'two','start':.5,'end':.7},
        {'word':'three','start':.8,'end':1.}],1.2,'whisperx',[1])
    assert payload['uncertain_words']==[1]
    assert payload['words'][0]['start']==.1
    base.write_textgrid(tmp_path/'sample.TextGrid',payload)
    tg=textgrid.openTextgrid(str(tmp_path/'sample.TextGrid'),includeEmptyIntervals=False)
    assert tg.getTier('words').entries[0].label=='one'
    assert len(tg.getTier('words').entries)==3
    payload['uncertain_words']=[3]
    with pytest.raises(ValueError,match='Uncertain index'):
        base.Alignment.model_validate(payload)


def test_cached_original_alignment_still_loads_model_for_new_asr(monkeypatch,tmp_path):
    from speecheval.align import whisperx_align as wx
    assert hasattr(wx,'get_align_model')
    model=object();metadata={'dictionary':{'A':1}}
    class Loader:
        calls=0
        def load_align_model(self,**kwargs):
            self.calls+=1
            return model,metadata
    loader=Loader()
    monkeypatch.setattr(wx,'_MODEL',None);monkeypatch.setattr(wx,'_METADATA',None)
    monkeypatch.setattr(wx,'_import_whisperx',lambda:loader)
    assert wx.get_align_model(tmp_path)==(model,metadata)
    assert wx.get_align_model(tmp_path)==(model,metadata)
    assert loader.calls==1
