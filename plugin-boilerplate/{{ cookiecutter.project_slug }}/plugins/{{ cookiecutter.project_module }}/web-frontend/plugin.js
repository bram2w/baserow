import { PluginNamePlugin } from '@{{ cookiecutter.project_slug }}/plugins'

export default (context) => {
  const { app } = context
  app.$registry.register('plugin', new PluginNamePlugin(context))
}
