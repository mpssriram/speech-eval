import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],server:{host:'0.0.0.0',port:5173,strictPort:true,
  watch:{usePolling:process.env.VITE_POLLING==='1'},proxy:{'/api':process.env.API_PROXY_URL||'http://127.0.0.1:8000'}}});
