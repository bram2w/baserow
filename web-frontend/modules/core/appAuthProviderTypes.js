import { Registerable } from '@baserow/modules/core/registry'

export class AppAuthProviderType extends Registerable {
  get name() {
    throw new Error('Must be set on the type.')
  }

  /**
   * The form to edit this user source.
   */
  get formComponent() {
    return null
  }

  getOrder() {
    return 0
  }
}
