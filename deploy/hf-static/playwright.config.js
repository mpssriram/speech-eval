import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./tests',testMatch:'*.spec.js',workers:1,timeout:180000,
 use:{baseURL:process.env.DEMO_BASE_URL||'http://127.0.0.1:18765',headless:true,viewport:{width:1440,height:1100},
 launchOptions:{args:['--autoplay-policy=no-user-gesture-required']},trace:'retain-on-failure'},
 webServer:process.env.DEMO_BASE_URL?undefined:{command:'npm run preview -- --port 18765',port:18765,reuseExistingServer:false},reporter:'list'});
