import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

/** A real prepared LibriVox take; no HTTP responses or scoring data are mocked. */
export function speechFixture(){
  const audio=process.env.UI_FIXTURE_AUDIO||path.resolve('../data/audio/hq/gettysburg__lv_mk__orig.wav');
  if(!fs.existsSync(audio))throw new Error(`UI fixture audio is missing: ${audio}. Restore the prepared dataset before running npm test. See reports/phase09_ui.md.`);
  return {audio,sha256:createHash('sha256').update(fs.readFileSync(audio)).digest('hex')};
}
export function reportPath(name:string){
  const filename=path.resolve('../reports',name);fs.mkdirSync(path.dirname(filename),{recursive:true});return filename;
}
