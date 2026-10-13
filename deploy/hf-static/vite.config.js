import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import {parse} from 'yaml';
import {detectorConfigPlugin} from '../../web/detectorConfigPlugin.js';
import path from 'node:path';
export default defineConfig({base:'./',plugins:[react(),detectorConfigPlugin(parse)],resolve:{dedupe:['react','react-dom'],alias:{
 'react':path.resolve('./node_modules/react'),
 'react-dom':path.resolve('./node_modules/react-dom'),
 '@mantine/core':path.resolve('./node_modules/@mantine/core'),
 '@mantine/hooks':path.resolve('./node_modules/@mantine/hooks'),
 'wavesurfer.js':path.resolve('./node_modules/wavesurfer.js'),
 'plotly.js-basic-dist':path.resolve('./node_modules/plotly.js-basic-dist')
}}});
