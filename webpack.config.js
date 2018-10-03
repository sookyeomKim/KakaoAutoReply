'use strict';
require('dotenv').config();
const path = require('path');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const S3Plugin = require('webpack-s3-plugin');


const workingDir = path.resolve(__dirname, 'static');

module.exports = {
    context: workingDir,
    mode: 'development',
    entry: {
        vendor: ['./js/vendor.js', './scss/vendor.scss'],
    },
    output: {
        path: workingDir + '/bundles',
        filename: '[name]-[chunkhash].js',
    },
    module: {
        rules: [{
            test: /\.scss$/,
            use: [
                MiniCssExtractPlugin.loader,
                {
                    loader: "css-loader",
                    options: {}
                },
                {
                    loader: "postcss-loader",
                    options: {
                        plugins: [
                            require('autoprefixer'),
                        ]
                    },
                },
                {
                    loader: "sass-loader",
                    options: {}
                }
            ]
        }],
    },
    plugins: [
        new CleanWebpackPlugin(workingDir + '/bundles'),
        new webpack.ProvidePlugin({
            Popper: ['popper.js', 'default']
        }),
        new BundleTracker({filename: './webpack-stats.json'}),
        new MiniCssExtractPlugin(
            {
                filename: '[name]-[chunkhash].css'
            }),
        new S3Plugin({
            s3Options: {
                accessKeyId: process.env.AWS_ACCESS_KEY_ID,
                secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
                region: 'ap-northeast-2'
            },
            s3UploadOptions: {
                Bucket: process.env.AWS_STORAGE_BUCKET_NAME
            },
            basePath: 'static/bundles'
        })
    ],
    optimization: {},
    resolve: {
        modules: ['node_modules'],
        extensions: ['.js', '.scss'],
    },
};