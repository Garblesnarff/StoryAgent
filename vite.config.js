import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    build: {
        outDir: 'static/dist',
        rollupOptions: {
            input: 'src/components/customize.jsx',
            external: ['react', 'react-dom', 'reactflow'],
            output: {
                entryFileNames: 'index.js',
                format: 'iife',
                globals: {
                    react: 'React',
                    'react-dom': 'ReactDOM',
                    reactflow: 'ReactFlow'
                }
            }
        }
    }
});
