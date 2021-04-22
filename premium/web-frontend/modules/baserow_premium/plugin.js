import { PremPlugin } from '@baserow_premium/plugins'

export default ({ app }) => {
  app.$registry.register('plugin', new PremPlugin())
}
