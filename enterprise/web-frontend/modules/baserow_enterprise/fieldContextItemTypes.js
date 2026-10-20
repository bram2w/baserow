import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { Registerable } from '@baserow/modules/core/registry'

const FieldPermissionsContextItem = lazyComponent(
  () =>
    import('@baserow_enterprise/components/fieldPermissions/FieldPermissionsContextItem')
)

export class FieldPermissionsContextItemType extends Registerable {
  static getType() {
    return 'field-permissions'
  }

  getComponent() {
    return FieldPermissionsContextItem
  }
}
