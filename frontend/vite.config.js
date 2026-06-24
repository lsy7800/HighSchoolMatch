import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    // Element Plus 整包引入, 单 chunk 偏大属预期, 抬高告警阈值
    chunkSizeWarningLimit: 1500,
  },
  server: {
    port: 5173,
    proxy: {
      // forward API + auth calls to FastAPI during dev
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
})
