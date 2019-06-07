const webpack = require('webpack');
const merge = require('webpack-merge');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

const webpackCommon = require('./webpack.common');
const config = require('./config');

const output = {
  path: config.dist,
  filename: config.jsFilename,
};

const plugins = [
  new CopyWebpackPlugin([
    {
      from: `${config.output}/assets/`,
      to: `${config.dist}/assets/`,
    },
  ]),
  new UglifyJsPlugin(),
  new webpack.LoaderOptionsPlugin({
    minimize: true,
  }),
];

const webpackConfig = {
  output,
  plugins,
};

module.exports = merge(webpackCommon, webpackConfig);
