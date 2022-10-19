import { Registerable } from '@baserow/modules/core/registry'

export class MembersPagePluginType extends Registerable {
  mutateMembersTableLeftColumns(leftColumns) {
    return leftColumns
  }

  mutateMembersTableRightColumns(rightColumns) {
    return rightColumns
  }

  mutateMembersInvitesTableRightColumns(rightColumns) {
    return rightColumns
  }

  mutateMembersInvitesTableLeftColumns(leftColumns) {
    return leftColumns
  }

  isDeactivated() {
    return true
  }
}
