"""Acoustic units and deterministic features on tiny synthetic recordings."""
import numpy as np
import pandas as pd
import pytest
from scipy.signal import butter, sosfiltfilt
from speecheval import features as f


def tone(amplitude=0.3):
    return amplitude*np.sin(2*np.pi*200*np.arange(44100)/44100)


def test_pitch_two_pass_recovers_200hz_and_semitones():
    frames,_=f.frame_tracks(tone(),44100,1.5)
    assert np.nanmedian(frames.f0_hz)==pytest.approx(200,abs=1)
    assert f.semitones(np.array([100.,200.]),100.).tolist()==[0.,12.]


def test_gain_halving_is_six_db_not_normalized_audio():
    first,_=f.frame_tracks(tone(),44100,1.5)
    second,_=f.frame_tracks(tone(.15),44100,1.5)
    assert np.nanmedian(second.intensity_db-first.intensity_db)==pytest.approx(-6.02,abs=.2)


def test_muffling_lowers_high_band_ratio():
    signal=np.random.default_rng(4).normal(0,.1,44100)
    low=sosfiltfilt(butter(4,1500,fs=44100,output='sos'),signal)
    dry,_=f.frame_tracks(signal,44100,1.5);wet,_=f.frame_tracks(low,44100,1.5)
    assert np.nanmedian(wet.hiband_ratio_db-dry.hiband_ratio_db)<-10


def test_syllables_and_rate_exclude_only_long_internal_pauses():
    assert [f.syllables(w) for w in ['Gettysburg','score','dedicated']]==[3,1,4]
    assert f.syllables('qxyz')>=1
    words=pd.DataFrame({'start':[0.,.3,1.],'end':[.2,.6,1.4],'syllables':[1,1,1]})
    assert f.window_rate(words,.25)==pytest.approx(3.)


def test_parquet_bytes_are_deterministic(tmp_path):
    frames,_=f.frame_tracks(tone(),44100,1.5)
    f.write_parquet(tmp_path/'a.parquet',frames)
    f.write_parquet(tmp_path/'b.parquet',frames)
    assert (tmp_path/'a.parquet').read_bytes()==(tmp_path/'b.parquet').read_bytes()


def test_octave_jumps_do_not_bridge_unvoiced_gaps():
    frames=pd.DataFrame({'f0_hz':[100.,200.,np.nan,100.,np.nan,200.],
                         'voiced':[True,True,False,True,False,True]})
    assert f.octave_jumps(frames)==1


def test_uncertain_words_excluded_from_speaker_stats_and_dependent_aggregates():
    t=np.arange(0,1.2,.01)
    data={'t':t,'f0_hz':np.where((t>=.4)&(t<.8),200.,100.),'voiced':True,
          'intensity_db':60.,'hnr_db':15.,'hiband_ratio_db':-10.,'centroid_hz':1000.}
    data.update({f'mfcc_{k}':0. for k in range(1,14)})
    frames=pd.DataFrame(data)
    words=[{'i':i,'norm':norm,'text':norm,'sentence':0,'start':i*.4,'end':(i+1)*.4} for i,norm in enumerate(['one','two','three'])]
    alignment={'recording_id':'sample','words':words,'uncertain_words':[1],
               'sentences':[{'i':0,'word_start':0,'word_end':2}]}
    w,windows,sentences,stats=f.aggregate_features(frames,alignment,{'pitch_floor_hz':60.,'pitch_ceiling_hz':600.},.25)
    assert stats['f0_median_hz']==100.
    assert np.isnan(w.loc[1,'f0_st_median'])
    assert np.isnan(w.loc[0,'pause_after_s'])
    assert np.isnan(w.loc[2,'pause_before_s'])
    assert windows.rate_syl_s.isna().all() and sentences.articulation_rate_syl_s.isna().all()


def test_zero_duration_sentence_does_not_inflate_speaker_rate():
    frames,_=f.frame_tracks(tone(),44100,1.5)
    words=[{'i':0,'text':'a','norm':'a','sentence':0,'start':.1,'end':.1},
           {'i':1,'text':'word','norm':'word','sentence':1,'start':.2,'end':.7}]
    alignment={'recording_id':'sample','words':words,'sentences':[
        {'i':0,'word_start':0,'word_end':0},{'i':1,'word_start':1,'word_end':1}]}
    _,windows,sentences,stats=f.aggregate_features(frames,alignment,{},.25)
    assert np.isnan(windows.loc[0,'rate_syl_s'])
    assert np.isnan(sentences.loc[0,'n_syllables'])
    assert stats['articulation_rate_syl_s']==2.
