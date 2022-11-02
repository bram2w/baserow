import { BaserowPlugin } from '@baserow/modules/core/plugins'

export class EnterprisePlugin extends BaserowPlugin {
  static getType() {
    return 'enterprise'
  }
}
