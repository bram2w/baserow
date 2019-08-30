const path = require('path');

const config = {
  'entry': path.join(__dirname, '../src'),
  'output':  path.join(__dirname, '../public'),
  'dist': path.join(__dirname, '../_build'),
  'host': '0.0.0.0',
  'port': 8080,
  'jsFilename': './baserow.js',
  'cssFilename': './baserow.css',
  'sourceMaps': true,
  'devtool': 'inline-source-map',
  'pages': ['index.html', 'login.html', 'grid.html', 'grid-s.html']
};

// Export config
module.exports = config;
