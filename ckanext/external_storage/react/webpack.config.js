const path = require('path')

const components = {
    'FileInputComponent':
        path.resolve(__dirname, 'components', 'FileInputComponent.js')
}

module.exports = {
    mode: 'production',
    target:'web',
    entry: components,
    output: {
        path: path.resolve('../webassets/js/'),
        filename: '[name].js'
    },
    devtool: 'eval-source-map',
    module: {
        rules: [
            {
                test: /\.(jsx|js)$/,
                exclude: /node_modules/,
                use: [{
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            [
                                '@babel/preset-env', {
                                    "targets": "defaults"
                                }
                            ],
                            '@babel/preset-react'
                        ]
                    }
                }]
            }
        ]
    }    
}
