import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const configPath=fileURLToPath(new URL('../configs/detector.yaml',import.meta.url));
/** Both dashboard builds read the actual detector configuration; scoring is untouched. */
export function detectorConfigPlugin(parse){
 const id='virtual:detector-config',resolved='\0'+id;
 return {name:'detector-config',resolveId(source){if(source===id)return resolved;},
  load(source){if(source!==resolved)return;this.addWatchFile(configPath);return 'export default '+JSON.stringify(parse(fs.readFileSync(configPath,'utf8')))+';';},
  handleHotUpdate({file,server}){if(file!==configPath)return;const module=server.moduleGraph.getModuleById(resolved);if(module){server.moduleGraph.invalidateModule(module);return [module];}}
 };
}
