import { Registerable } from '@baserow/modules/core/registry'

export class MembersPagePluginType extends Registerable {
  /**
   * Lets you manipulate the left columns of the members table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersTableLeftColumns(leftColumns, context) {
    return leftColumns
  }

  /**
   * Lets you manipulate the right columns of the members table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersTableRightColumns(rightColumns, context) {
    return rightColumns
  }

  /**
   * Lets you manipulate the right columns of the invites table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersInvitesTableRightColumns(rightColumns, context) {
    return rightColumns
  }

  /**
   * Lets you manipulate the left columns of the invites table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersInvitesTableLeftColumns(leftColumns, context) {
    return leftColumns
  }

  /**
   * Set to false in order to enable the plugin
   */
  isDeactivated() {
    return !this.app.$featureFlags.includes('roles') // TODO make this depending on if somebody has RBAc
  }
}
