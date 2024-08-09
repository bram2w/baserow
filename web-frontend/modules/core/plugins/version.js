const pkg = require('../package.json')

export default (context, inject) => {
  inject('baserowVersion', pkg.version)
}
