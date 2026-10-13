import type {Region,Word} from './types';
export function fixed(value:number,digits?:number):string;
export function timeRange(start:number,end:number):string;
export function formatText(text:unknown):string;
export function formatExplanation(region:Region,words:Pick<Word,'i'|'text'>[],mode?:string,threshold?:number):string;

export function flagThreshold(config:{k:Record<string,number>;mode_c:{k:Record<string,number>}},type:string,mode?:string):number;
export function sdTooltip(threshold:number):string;
