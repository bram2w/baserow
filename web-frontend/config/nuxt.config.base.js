export default function (base = '@') {
  return {
    modules: [
      base + '/modules/core/module.js',
      base + '/modules/database/module.js',
    ],
  }
}
