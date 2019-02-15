const ExtractTextPlugin = require('extract-text-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const autoprefixer = require('autoprefixer');

const config = require('./config');

const entry = {
  baserow: config.entry,
};

/**
 * Array of resolve modules entry and file extension to prevent ESLint errors.
 */
const resolve = {
  modules: [config.entry, 'node_modules'],
  extensions: ['*', '.js', '.json'],
};

const modules = {
  rules: [
    {
      test: /\.js$/,
      exclude: /node_modules/,
      use: [
        {
          loader: 'babel-loader?cacheDirectory',
          options: {
            presets: ['@babel/preset-env'],
          },
        },
        {
          loader: 'eslint-loader',
        },
      ],
    },
    {
      test: /\.css$/,
      exclude: /node_modules/,
      use: ExtractTextPlugin.extract({
        fallback: 'style-loader',
        use: [
          {
            loader: 'css-loader',
            options: {
              sourceMap: config.sourceMaps,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              ident: 'postcss',
              plugins: () => [
                autoprefixer({
                  browsers: ['last 5 versions'],
                }),
              ],
              sourceMap: 'inline',
            },
          },
        ],
      }),
    },
    {
      test: /\.(woff|woff2|eot|ttf|svg|ico|jpg|jpeg|png)$/,
      loader: 'url-loader?limit=1000000',
    },
    {
      test: /\.scss$/,
      exclude: /node_modules/,
      use: ExtractTextPlugin.extract({
        fallback: 'style-loader',
        use: [
          {
            loader: 'css-loader',
            options: {
              sourceMap: config.sourceMaps,
            },
          },
          {
            loader: 'postcss-loader',
            options: {
              ident: 'postcss',
              plugins: () => [
                autoprefixer({
                  browsers: ['last 5 versions'],
                }),
              ],
              sourceMap: 'inline',
            },
          },
          {
            loader: 'sass-loader',
            options: {
              sourceMap: config.sourceMaps,
            },
          },
        ],
      }),
    },
    {
      test: /\.html$/,
      exclude: /node_modules/,
      loader: 'raw-loader',
    },
  ],
};

const plugins = [
  new CleanWebpackPlugin([config.dist], {
    allowExternal: true,
  }),
  new ExtractTextPlugin(config.cssFilename),
  new HtmlWebpackPlugin({
    template: `${config.output}/index.html`,
  }),
];

const webpackConfig = {
  entry,
  resolve,
  module: modules,
  plugins,
};

module.exports = webpackConfig;
