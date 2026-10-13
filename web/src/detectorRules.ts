import config from 'virtual:detector-config';
import {flaws,type FlawType} from './types';
/** Describe the configured rule in the selected mode, including inclusive cutoffs. */
export function detectorRule(type:FlawType,mode:string):string {
 const label=flaws[type].label;
 if(mode==='C'){
  const features:Partial<Record<FlawType,[string,string,string]>>={rushing:['rate','sentence speech rate','above'],dragging:['rate','sentence speech rate','below'],monotone:['pitchrange','sentence pitch range','below'],too_quiet:['final_drop','sentence-end loudness drop','below'],missing_pause:['end_pause','sentence-end pause','below']};
  const feature=features[type];
  return feature?`${label} is flagged when ${feature[1]} is at least ${config.mode_c.k[feature[0]]} robust SD ${feature[2]} good-speaker norms.`:`${label} is not evaluated by Mode C’s four-feature norms.`;
 }
 const k=config.k[type];
 if(type==='awkward_pause')return `${label} is flagged when a pause is at least ${k} SD above the reference and lasts at least ${config.awkward_pause_min_s} s.`;
 if(type==='missing_pause')return `${label} is flagged when a pause is at least ${k} SD below the reference, the reference pause is at least ${config.missing_pause_ref_min_s} s, and yours is at most ${config.missing_pause_max_frac*100}% of it.`;
 const measures:Partial<Record<FlawType,[string,string]>>={rushing:['speech rate','above'],dragging:['speech rate','below'],monotone:['pitch variation','below'],too_quiet:['loudness','below'],mumbling:['clarity','below']};
 const measure=measures[type]!;
 return `${label} is flagged when ${measure[0]} is at least ${k} SD ${measure[1]} the reference across at least ${config.region_min_words} flagged words in a sentence.`;
}
