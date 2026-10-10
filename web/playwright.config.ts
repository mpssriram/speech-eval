import { defineConfig } from '@playwright/test';
export default defineConfig({testDir:'./tests',workers:1,timeout:180000,use:{baseURL:process.env.UI_BASE_URL||'http://localhost:5173',headless:true,
  viewport:{width:1440,height:1000},launchOptions:{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,
    args:['--use-fake-device-for-media-stream','--use-fake-ui-for-media-stream']},
  trace:'retain-on-failure'},reporter:'list'});
