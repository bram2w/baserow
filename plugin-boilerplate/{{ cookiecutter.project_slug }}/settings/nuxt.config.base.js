import base from '/baserow/web-frontend/config/nuxt.config.base.js'

const baseConfig = base('/baserow/web-frontend')
baseConfig.modules.push('../plugins/{{ cookiecutter.project_module }}/web-frontend/module.js')

export default baseConfig
