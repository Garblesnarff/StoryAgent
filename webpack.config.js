const path = require('path');

module.exports = {
    mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
    entry: {
        main: './static/js/customize.js',
        effectLibrary: './static/js/components/effect-library.js'
    },
    output: {
        path: path.resolve(__dirname, 'static/dist'),
        filename: '[name].bundle.js',
        publicPath: '/static/dist/'
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            ['@babel/preset-react', { runtime: 'automatic' }]
                        ],
                        plugins: ['@babel/plugin-transform-runtime']
                    }
                }
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            }
        ]
    },
    resolve: {
        extensions: ['.js', '.jsx'],
        alias: {
            '@dnd-kit/core': path.resolve(__dirname, 'node_modules/@dnd-kit/core'),
            '@dnd-kit/sortable': path.resolve(__dirname, 'node_modules/@dnd-kit/sortable'),
            '@dnd-kit/utilities': path.resolve(__dirname, 'node_modules/@dnd-kit/utilities'),
            '@dnd-kit/modifiers': path.resolve(__dirname, 'node_modules/@dnd-kit/modifiers'),
            'react': path.resolve(__dirname, 'node_modules/react'),
            'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
            'reactflow': path.resolve(__dirname, 'node_modules/reactflow')
        }
    },
    optimization: {
        splitChunks: {
            chunks: 'all',
        },
    },
    performance: {
        hints: false
    },
    devtool: process.env.NODE_ENV === 'production' ? false : 'source-map'
};
