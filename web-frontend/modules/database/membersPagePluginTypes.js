import { Registerable } from '@baserow/modules/core/registry'

export class MembersPagePluginType extends Registerable {
  /**
   * Lets you manipulate the left columns of the members table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersTableLeftColumns(leftColumns) {
    return leftColumns
  }

  /**
   * Lets you manipulate the right columns of the members table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersTableRightColumns(rightColumns) {
    return rightColumns
  }

  /**
   * Lets you manipulate the right columns of the invites table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersInvitesTableRightColumns(rightColumns) {
    return rightColumns
  }

  /**
   * Lets you manipulate the left columns of the invites table to either add, remove
   * or modify columns.
   *
   * You could always make sure to not make this function fail hard if it can't update
   * or remove something, since other plugins might have also altered the columns.
   */
  mutateMembersInvitesTableLeftColumns(leftColumns) {
    return leftColumns
  }

  /**
   * Set to false in order to enable the plugin
   */
  isDeactivated() {
    return true
  }
}
