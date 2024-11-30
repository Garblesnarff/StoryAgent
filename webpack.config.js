/**
 * Webpack Configuration
 * 
 * This configuration file sets up the build process for the React/TypeScript
 * frontend application. It handles TypeScript compilation, CSS processing,
 * and asset bundling.
 * 
 * Key Features:
 * - TypeScript and React/JSX support
 * - CSS processing with PostCSS and Tailwind
 * - Source map generation for debugging
 * - Path aliases for clean imports
 * - Development mode with enhanced debugging
 */

const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
    // Development mode for better debugging and faster builds
    mode: 'development',

    // Main application entry point
    entry: './src/index.tsx',

    // Output configuration for bundled files
    output: {
        path: path.resolve(__dirname, 'static/dist'),
        filename: 'bundle.js',
        publicPath: '/static/dist/'
    },

    // Configure module resolution and imports
    resolve: {
        // File extensions to handle (order matters for performance)
        extensions: ['.ts', '.tsx', '.js', '.jsx'],
        // Path aliases for cleaner imports (e.g., @/components)
        alias: {
            '@': path.resolve(__dirname, 'src'),
        }
    },

    // Module rules for different file types
    module: {
        rules: [
            // TypeScript and React/JSX processing
            {
                test: /\.(ts|tsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'ts-loader'
                }
            },
            // CSS processing pipeline
            {
                test: /\.css$/,
                use: [
                    // Extract CSS into separate files
                    MiniCssExtractPlugin.loader,
                    // Process CSS imports
                    'css-loader',
                    // Apply PostCSS transformations
                    'postcss-loader'
                ]
            }
        ]
    },

    // Plugins for additional processing
    plugins: [
        // Extract CSS into separate files
        new MiniCssExtractPlugin({
            filename: 'main.css'
        })
    ],

    // Source map generation for debugging
    devtool: 'source-map'
};
