import type {Region,Word} from './types';
export function fixed(value:number,digits?:number):string;
export function timeRange(start:number,end:number):string;
export function formatText(text:unknown):string;
export function formatExplanation(region:Region,words:Pick<Word,'i'|'text'>[],mode?:string):string;
