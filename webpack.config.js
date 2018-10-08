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
                    options: {
                        //scss 내부에 이미지를 불러오고 있으나 해당 이미지가 없어
                        //ModuleNotFoundError: Module not found: Error: Can't resolve '../../img/arrow-left.cur' in '/Users/kimsookyeom/PycharmProjects/KakaoAutoReply/static/scss'
                        //위의 에러를 발생시킨다...
                        //사용상에 문제는 없는데 이것때문에 컴파일이 안 된다.
                        //url핸들링을 꺼버리자
                        url: false

                    }
                },
                // {
                //     loader: "resolve-url-loader",
                //     options: {}
                // },
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
            Popper: ['popper.js', 'default'],
            moment: ['moment']
        }),
        new BundleTracker({filename: './webpack-stats.json'}),
        new MiniCssExtractPlugin(
            {
                filename: '[name]-[chunkhash].css',
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
        extensions: ['.js', '.scss', 'css'],
        alias: {
            'nouislider': 'material-kit/assets/js/plugins/nouislider.min',
            'sharrre': 'material-kit/assets/js/plugins/jquery.sharrre',
            'bootstrap-datetimepicker': 'material-kit/assets/js/plugins/bootstrap-datetimepicker',

            'bootstrap-material-design': 'material-kit/assets/js/core/bootstrap-material-design.min',

            'material-kit.js': 'material-kit/assets/js/material-kit'
        }
    },
};