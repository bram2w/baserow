import { BaserowPlugin } from '@baserow/modules/core/plugins'

export class PremiumPlugin extends BaserowPlugin {
  static getType() {
    return 'plugin'
  }
}
