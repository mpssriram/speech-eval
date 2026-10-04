# Day 1 automatic acoustic verification

This replaces unavailable human listening review; it is not human-verified ground truth.
CTC sums all valid monotonic alignment paths for each candidate, then divides the total log-likelihood by the same audio frame count. CPU wav2vec2, evaluation mode, fixed seed and one thread.
Method references: [PyTorch CTCLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CTCLoss.html) and [torchaudio wav2vec2 forced alignment](https://docs.pytorch.org/audio/stable/tutorials/forced_alignment_tutorial.html).

Margin: 0.050 nats/frame. Positive delta favors candidate B.
Decisions: {'APPLY_B': 6, 'KEEP_A': 17, 'UNSURE': 62}

Both ASRs agreeing is supporting evidence only; acoustic preference must still meet the margin. Non-finite alignments and small margins remain UNSURE; no text is deleted merely because a candidate cannot align.

## Distribution of B minus A

| Statistic | Nats/frame |
|---|---:|
| min | -3.934342 |
| p10 | -2.712631 |
| p25 | 0.000358 |
| median | 0.017185 |
| p75 | 0.032221 |
| p90 | 0.047313 |
| max | 0.211645 |

| Delta range | Items |
|---|---:|
| below -0.10 | 15 |
| -0.10 to -0.05 | 2 |
| -0.05 to 0 | 4 |
| 0 to 0.05 | 58 |
| 0.05 to 0.10 | 3 |
| at least 0.10 | 3 |

| Original ASR class | APPLY_B | KEEP_A | UNSURE |
|---|---:|---:|---:|
| LISTEN | 5 | 8 | 40 |
| LIKELY_REAL | 1 | 9 | 22 |

The 0.05 margin is a provisional operating threshold, not a calibrated confidence level. This unlabeled score distribution shows its selectivity but cannot establish error rates or justify accuracy claims. Longer sentences dilute local differences; related acoustic models can share errors. UNSURE remains unresolved.

Verification covers the frozen original 85 listen-list items. Correcting the truncated poem audio exposes additional full-poem differences in day01_transcript_diffs.md; these are not silently claimed verified. Edge insertions such as year/readout words remain model preferences on retained boundary audio, not proof of complete spoken words.

## Prepared-audio corrections

- o_captain__lv_apc__orig: end 45.959s → 121.611s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_chip__orig: end 42.289s → 109.772s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_foxits__orig: end 42.291s → 106.348s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_jtm__orig: end 44.770s → 109.761s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_mac__orig: end 31.564s → 80.727s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_mb__orig: end 45.762s → 102.072s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_md__orig: end 61.378s → 142.732s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_rg__orig: end 63.692s → 125.473s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_s__orig: end 38.800s → 97.716s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_sjs__orig: end 39.866s → 107.820s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_ss__orig: end 43.560s → 106.284s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.
- o_captain__lv_th__orig: end 32.766s → 86.466s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.

## Every input listen-list item

| Recording | Original time | Sentence window | Transcript says | ASR variant | ASR class | Score A | Score B | B − A | Decision |
|---|---:|---|---|---|---|---:|---:|---:|---|
| gettysburg__lv_amb__orig | 0.000s | 0.000–14.551s | — | Boulay. | LISTEN | -0.104118 | -0.167542 | -0.063424 | KEEP_A |
| gettysburg__lv_amb__orig | 5.898s | 0.000–14.551s | on | upon | LIKELY_REAL | -0.104118 | -0.082970 | 0.021148 | UNSURE |
| gettysburg__lv_amb__orig | 35.132s | 27.262–36.753s | that | this | LIKELY_REAL | -0.287447 | -0.234528 | 0.052919 | APPLY_B |
| gettysburg__lv_amb__orig | 104.788s | 74.618–105.738s | the | this | LISTEN | -0.034445 | -0.020721 | 0.013724 | UNSURE |
| gettysburg__lv_dj__orig | 3.454s | 0.000–10.701s | on | upon | LISTEN | -0.082406 | -0.063091 | 0.019315 | UNSURE |
| gettysburg__lv_dj__orig | 29.868s | 23.242–31.329s | that | this | LIKELY_REAL | -0.110458 | -0.067618 | 0.042840 | UNSURE |
| gettysburg__lv_dj__orig | 46.304s | 42.981–48.966s | it | — | LISTEN | -0.170707 | -0.141288 | 0.029419 | UNSURE |
| gettysburg__lv_dj__orig | 53.858s | 49.087–55.941s | it | I | LISTEN | -0.132690 | -0.130644 | 0.002045 | UNSURE |
| gettysburg__lv_dj__orig | 96.718s | 66.078–102.880s | the | this | LISTEN | -0.367711 | -0.362312 | 0.005398 | UNSURE |
| gettysburg__lv_dl__orig | 4.455s | 0.000–13.426s | on | upon | LIKELY_REAL | -0.044168 | -0.019726 | 0.024442 | UNSURE |
| gettysburg__lv_dl__orig | 38.041s | 28.098–39.723s | that | this | LISTEN | -0.193292 | -0.160120 | 0.033172 | UNSURE |
| gettysburg__lv_dl__orig | 51.492s | 44.489–53.154s | can not hallow | cannot hollow | LIKELY_REAL | -0.165985 | -0.142281 | 0.023703 | UNSURE |
| gettysburg__lv_dl__orig | 117.529s | 84.200–125.478s | the | this | LISTEN | -0.410823 | -0.405437 | 0.005385 | UNSURE |
| gettysburg__lv_eep__orig | 5.097s | 0.951–15.591s | on | upon | LIKELY_REAL | -0.230049 | -0.212864 | 0.017185 | UNSURE |
| gettysburg__lv_eep__orig | 43.817s | 35.289–45.959s | that | this | LIKELY_REAL | -0.155670 | -0.122867 | 0.032803 | UNSURE |
| gettysburg__lv_eep__orig | 144.421s | 101.401–154.869s | the | this | LISTEN | -0.255650 | -0.252222 | 0.003428 | UNSURE |
| gettysburg__lv_fb__orig | 5.278s | 0.000–14.131s | on | upon | LIKELY_REAL | -0.042720 | -0.025140 | 0.017580 | UNSURE |
| gettysburg__lv_fb__orig | 34.952s | 25.830–36.464s | that | this | LISTEN | -0.168059 | -0.131418 | 0.036642 | UNSURE |
| gettysburg__lv_fb__orig | 46.688s | 41.161–48.770s | can not hallow | cannot hollow | LIKELY_REAL | -0.182755 | -0.159342 | 0.023413 | UNSURE |
| gettysburg__lv_fb__orig | 77.636s | 75.674–114.928s | here | — | LISTEN | -0.348473 | -0.305857 | 0.042616 | UNSURE |
| gettysburg__lv_fb__orig | 78.838s | 75.674–114.928s | — | of | LISTEN | -0.348473 | -0.342350 | 0.006123 | UNSURE |
| gettysburg__lv_fb__orig | 109.661s | 75.674–114.928s | the | this | LISTEN | -0.348473 | -0.347129 | 0.001344 | UNSURE |
| gettysburg__lv_jn__orig | 4.735s | 0.000–13.382s | on | upon | LIKELY_REAL | -0.093957 | -0.064317 | 0.029640 | UNSURE |
| gettysburg__lv_jn__orig | 34.628s | 27.701–36.250s | that | this | LISTEN | -0.147786 | -0.100101 | 0.047685 | UNSURE |
| gettysburg__lv_jn__orig | 105.610s | 76.994–106.541s | the | this | LIKELY_REAL | -0.030820 | -0.017226 | 0.013594 | UNSURE |
| gettysburg__lv_law__orig | 10.041s | 0.000–17.570s | on | upon | LISTEN | -1.111968 | -1.095745 | 0.016223 | UNSURE |
| gettysburg__lv_law__orig | 38.888s | 30.734–40.610s | that | this | LISTEN | -0.261791 | -0.214532 | 0.047259 | UNSURE |
| gettysburg__lv_law__orig | 105.533s | 77.646–106.404s | the | this | LIKELY_REAL | -0.036056 | -0.018379 | 0.017678 | UNSURE |
| gettysburg__lv_lb__orig | 0.000s | 0.000–17.835s | — | b | LISTEN | -0.085046 | -0.059575 | 0.025471 | UNSURE |
| gettysburg__lv_lb__orig | 6.700s | 0.000–17.835s | on | upon | LIKELY_REAL | -0.085046 | -0.062671 | 0.022375 | UNSURE |
| gettysburg__lv_lb__orig | 47.159s | 37.309–49.342s | that | this | LISTEN | -0.106710 | -0.063379 | 0.043331 | UNSURE |
| gettysburg__lv_lb__orig | 145.656s | 103.459–155.065s | the | this | LISTEN | -0.396017 | -0.390713 | 0.005304 | UNSURE |
| gettysburg__lv_mas__orig | 5.858s | 0.000–18.534s | on | upon | LIKELY_REAL | -0.039376 | -0.020474 | 0.018902 | UNSURE |
| gettysburg__lv_mas__orig | 58.978s | 45.209–61.820s | that | this | LIKELY_REAL | -0.085024 | -0.061084 | 0.023940 | UNSURE |
| gettysburg__lv_mas__orig | 190.057s | 136.500–190.948s | the | this | LIKELY_REAL | -0.012301 | -0.004030 | 0.008271 | UNSURE |
| gettysburg__lv_mk__orig | 4.134s | 0.000–13.242s | on | upon | LISTEN | -0.040694 | -0.024479 | 0.016215 | UNSURE |
| gettysburg__lv_mk__orig | 38.009s | 29.560–39.270s | that | this | LISTEN | -0.115850 | -0.073890 | 0.041960 | UNSURE |
| gettysburg__lv_mk__orig | 113.476s | 81.082–120.976s | the | this | LISTEN | -0.408969 | -0.402451 | 0.006519 | UNSURE |
| gettysburg__lv_pc__orig | 4.155s | 0.000–13.046s | on | upon | LIKELY_REAL | -0.081457 | -0.058543 | 0.022914 | UNSURE |
| gettysburg__lv_pc__orig | 36.666s | 28.535–38.509s | that | this | LISTEN | -0.135520 | -0.093697 | 0.041823 | UNSURE |
| gettysburg__lv_pc__orig | 50.402s | 43.477–52.343s | can not hallow | cannot hollow | LIKELY_REAL | -0.151286 | -0.127542 | 0.023744 | UNSURE |
| gettysburg__lv_pc__orig | 113.687s | 82.969–124.735s | — | and | LIKELY_REAL | -0.446391 | -0.431140 | 0.015250 | UNSURE |
| gettysburg__lv_pc__orig | 116.852s | 82.969–124.735s | the | this | LISTEN | -0.446391 | -0.440770 | 0.005621 | UNSURE |
| gettysburg__lv_rk__orig | 4.858s | 0.000–13.893s | on | upon | LISTEN | -0.102105 | -0.092774 | 0.009331 | UNSURE |
| gettysburg__lv_rk__orig | 9.126s | 0.000–13.893s | and | — | LISTEN | -0.102105 | -0.071739 | 0.030366 | UNSURE |
| gettysburg__lv_rk__orig | 38.342s | 29.229–40.265s | that | this | LISTEN | -0.218849 | -0.191897 | 0.026952 | UNSURE |
| gettysburg__lv_rk__orig | 65.051s | 63.590–72.840s | note | — | LISTEN | -0.108720 | -0.144230 | -0.035510 | UNSURE |
| gettysburg__lv_rk__orig | 120.963s | 83.916–129.366s | the | this | LISTEN | -0.271688 | -0.267728 | 0.003961 | UNSURE |
| gettysburg__lv_sa__orig | 4.215s | 0.000–15.169s | on | upon | LISTEN | -0.063293 | -0.042970 | 0.020323 | UNSURE |
| gettysburg__lv_sa__orig | 41.527s | 30.823–43.289s | that | this | LISTEN | -0.175459 | -0.143238 | 0.032221 | UNSURE |
| gettysburg__lv_sa__orig | 81.370s | 79.833–93.305s | It | — | LISTEN | -0.139372 | -0.202561 | -0.063189 | KEEP_A |
| gettysburg__lv_tg__orig | 3.814s | 0.000–12.083s | on | upon | LISTEN | -0.166862 | -0.138947 | 0.027915 | UNSURE |
| gettysburg__lv_tg__orig | 10.642s | 0.000–12.083s | are | were | LISTEN | -0.166862 | -0.125873 | 0.040989 | UNSURE |
| gettysburg__lv_tg__orig | 13.224s | 12.364–22.314s | are | have | LIKELY_REAL | -0.194352 | -0.146368 | 0.047984 | UNSURE |
| gettysburg__lv_tg__orig | 32.828s | 25.919–34.470s | that | this | LIKELY_REAL | -0.125950 | -0.078600 | 0.047349 | UNSURE |
| gettysburg__lv_tg__orig | 102.678s | 73.201–109.496s | the | this | LISTEN | -0.550640 | -0.546322 | 0.004318 | UNSURE |
| gettysburg__lv_wt__orig | 4.757s | 0.832–14.370s | on | upon | LISTEN | -0.186018 | -0.165188 | 0.020830 | UNSURE |
| gettysburg__lv_wt__orig | 40.915s | 32.622–43.138s | that | this | LISTEN | -0.114619 | -0.076630 | 0.037989 | UNSURE |
| gettysburg__lv_wt__orig | 125.069s | 87.880–126.000s | the | this | LIKELY_REAL | -0.024170 | -0.012066 | 0.012105 | UNSURE |
| jfk_rice__jfk__orig | 5.475s | 7.978–16.307s | — | We choose to go to the moon. | LISTEN | -0.180870 | -0.383195 | -0.202325 | KEEP_A |
| jfk_rice__jfk__orig | 38.896s | 16.007–41.460s | which | — | LIKELY_REAL | -0.164229 | -0.124786 | 0.039444 | UNSURE |
| jfk_rice__jfk__orig | 150.222s | 142.771–157.632s | — | The Mariner spacecraft | LISTEN | -0.315666 | -0.226379 | 0.089287 | APPLY_B |
| o_captain__lv_apc__orig | 0.000s | 0.000–7.500s | — | 2006. | LISTEN | -0.581357 | -0.369713 | 0.211645 | APPLY_B |
| o_captain__lv_apc__orig | 33.102s | 33.102–109.304s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.045328 | -2.723235 | -2.677907 | KEEP_A |
| o_captain__lv_chip__orig | 41.242s | 41.263–109.316s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.049092 | -2.784873 | -2.735781 | KEEP_A |
| o_captain__lv_foxits__orig | 27.597s | 27.617–92.244s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LISTEN | -0.247344 | -3.340778 | -3.093434 | KEEP_A |
| o_captain__lv_jtm__orig | 31.686s | 31.677–97.208s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.053865 | -3.076057 | -3.022193 | KEEP_A |
| o_captain__lv_mac__orig | 20.821s | 22.530–70.595s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LISTEN | -0.031568 | -3.965910 | -3.934342 | KEEP_A |
| o_captain__lv_mb__orig | 25.048s | 25.029–81.869s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LISTEN | -0.050915 | -3.495786 | -3.444871 | KEEP_A |
| o_captain__lv_md__orig | 31.144s | 33.207–113.028s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.253694 | -2.236714 | -1.983020 | KEEP_A |
| o_captain__lv_mrg__orig | 11.225s | 7.420–12.286s | all | are | LISTEN | -0.592391 | -0.468963 | 0.123428 | APPLY_B |
| o_captain__lv_mrg__orig | 25.716s | 24.835–27.137s | cold | pulled, | LISTEN | -0.510770 | -0.625362 | -0.114592 | KEEP_A |
| o_captain__lv_mrg__orig | 86.202s | 82.651–86.412s | — | End | LISTEN | -0.379534 | -0.215031 | 0.164503 | APPLY_B |
| o_captain__lv_rg__orig | 15.604s | 14.504–19.127s | eyes | I as | LISTEN | -0.259319 | -0.450964 | -0.191645 | KEEP_A |
| o_captain__lv_rg__orig | 29.598s | 31.566–92.089s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.027285 | -3.418687 | -3.391402 | KEEP_A |
| o_captain__lv_s__orig | 27.655s | 27.335–86.761s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | Oh, | LIKELY_REAL | -0.064675 | -3.808417 | -3.743743 | KEEP_A |
| o_captain__lv_sjs__orig | 21.589s | 18.337–25.674s | heart!          O | Hot! Oh, | LISTEN | -0.140102 | -0.180511 | -0.040410 | UNSURE |
| o_captain__lv_sjs__orig | 29.539s | 29.509–97.983s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.086866 | -2.427332 | -2.340466 | KEEP_A |
| o_captain__lv_ss__orig | 24.054s | 25.295–87.288s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | — | LIKELY_REAL | -0.427181 | -3.428747 | -3.001566 | KEEP_A |
| o_captain__lv_th__orig | 24.604s | 24.264–78.534s | O Captain! my Captain! rise up and hear the bells; Rise up- for you the flag is flung- for you the bugle trills, For you bouquets and ribbon’d wreaths- for you the shores a-crowding, For you they call, the swaying mass, their eager faces turning;        Here Captain! dear father!          This arm beneath your head!            It is some dream that on the deck,              You’ve fallen cold and dead. My Captain does not answer, his lips are pale and still, My father does not feel my arm, he has no pulse nor will, The ship is anchor’d safe and sound, its voyage closed and done, From fearful trip the victor ship comes in with object won;        Exult O shores, and ring O bells!          But I with mournful tread,            Walk the deck my Captain lies,              Fallen cold and dead | Oh, | LIKELY_REAL | -0.056186 | -3.522587 | -3.466401 | KEEP_A |
| reagan_challenger__reagan__orig | 20.163s | 17.920–21.505s | of | — | LISTEN | -0.101234 | -0.049851 | 0.051383 | APPLY_B |
| reagan_challenger__reagan__orig | 52.695s | 50.892–62.993s | Dick Scobee | Nick Scobie, | LISTEN | -0.104300 | -0.103942 | 0.000358 | UNSURE |
| reagan_challenger__reagan__orig | 66.138s | 64.596–71.926s | For | — | LISTEN | -0.180870 | -0.184975 | -0.004106 | UNSURE |
| reagan_challenger__reagan__orig | 214.902s | 211.658–221.088s | an | the | LISTEN | -0.062583 | -0.065682 | -0.003099 | UNSURE |
| reagan_challenger__reagan__orig | 232.610s | 229.806–234.693s | by | for | LISTEN | -0.090041 | -0.076954 | 0.013086 | UNSURE |
