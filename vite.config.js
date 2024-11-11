import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'static/dist',
    assetsDir: '',
    rollupOptions: {
      input: 'src/components/customize.jsx',
      output: {
        entryFileNames: 'index.js',
        chunkFileNames: '[name].[hash].js',
        assetFileNames: 'index.[ext]'
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
