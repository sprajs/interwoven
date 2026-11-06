import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { researchSync } from './scripts/research-sync.ts'

export default defineConfig({
  plugins: [react(), tailwindcss(), researchSync()],
  server: { port: 5174, strictPort: true },
})
