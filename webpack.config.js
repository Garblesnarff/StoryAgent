const path = require('path');

module.exports = {
    mode: 'development',
    entry: './src/App.tsx',
    output: {
        path: path.resolve(__dirname, 'static/dist'),
        filename: 'bundle.js',
        publicPath: '/static/dist/'
    },
    resolve: {
        extensions: ['.ts', '.tsx', '.js', '.jsx'],
        alias: {
            '@': path.resolve(__dirname, 'src'),
        }
    },
    module: {
        rules: [
            {
                test: /\.(ts|tsx)$/,
                exclude: /node_modules/,
                use: {
                    loader: 'ts-loader'
                }
            },
            {
                test: /\.css$/,
                use: [
                    'style-loader',
                    'css-loader',
                    'postcss-loader'
                ]
            }
        ]
    },
    devtool: 'source-map'
};
