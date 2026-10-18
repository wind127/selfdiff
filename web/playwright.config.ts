import {defineConfig} from 'playwright/test';
export default defineConfig({
  testDir:'./e2e', workers:1, timeout:30000, use:{baseURL:'http://127.0.0.1:8770',headless:true},
  webServer:{command:`"${process.env.SELFDIFF_PYTHON || (process.platform==='win32'?'../.venv/Scripts/python.exe':'python')}" ../tests/serve_e2e.py`,url:'http://127.0.0.1:8770/api/health',reuseExistingServer:false,timeout:30000},
});
