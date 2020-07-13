import { PluginNamePlugin } from '@{{ cookiecutter.project_slug }}/plugins'

export default ({ store, app }) => {
  app.$registry.register('plugin', new PluginNamePlugin())
}
