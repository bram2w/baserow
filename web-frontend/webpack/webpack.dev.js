const merge = require('webpack-merge');

const webpackCommon = require('./webpack.common');
const config = require('./config');

const output = {
  path: config.output,
  filename: config.jsFilename,
};

const devServer = {
  contentBase: config.output,
  host: config.host,
  port: config.port,
};

const webpackConfig = {
  output,
  devServer,
  watch: true,
  devtool: config.devtool
};

module.exports = merge(webpackCommon, webpackConfig);
