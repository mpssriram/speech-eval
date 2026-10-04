"""Deterministic CPU WhisperX wav2vec2 forced alignment, without ASR inference."""
import os
from pathlib import Path
from typing import Any
import torch
from speecheval.align.base import make_alignment
from speecheval.prepare import _import_whisperx

_MODEL: Any = None
_METADATA: Any = None


def get_align_model(root: Path) -> tuple[Any,Any]:
    """Lazy CPU model even when all previous transcript alignments were cached."""
    global _MODEL,_METADATA
    os.environ['HF_HOME']=str(root/'data/.cache/huggingface')
    os.environ['TORCH_HOME']=str(root/'data/.cache/torch')
    if _MODEL is None:
        _MODEL,_METADATA=_import_whisperx().load_align_model(language_code='en',device='cpu',model_dir=str(root/'data/.cache/torch'))
    return _MODEL,_METADATA


def align_recording(root: Path, rid: str, body: str, windows: list[dict[str,Any]], duration: float,
                    uncertain: list[int] | None = None) -> dict[str,Any]:
    """Align supplied transcript sentences against mono 16 kHz audio on CPU."""
    global _MODEL,_METADATA
    os.environ['HF_HOME']=str(root/'data/.cache/huggingface')
    os.environ['TORCH_HOME']=str(root/'data/.cache/torch')
    torch.manual_seed(0);torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    wx=_import_whisperx()
    _MODEL,_METADATA=get_align_model(root)
    torch.backends.mkldnn.enabled=False;torch.backends.mha.set_fastpath_enabled(False)
    torch.set_float32_matmul_precision('highest');torch.set_flush_denormal(False)
    segments=[{'text':w['text'],'start':w['start'],'end':w['end']} for w in windows if w['valid']]
    result=wx.align(segments,_MODEL,_METADATA,str(root/'data/audio/align16k'/f'{rid}.wav'),'cpu',print_progress=False)
    output=[word for segment in result['segments'] for word in segment.get('words',[])]
    return make_alignment(rid,body,windows,output,duration,'whisperx',uncertain)
