import { Registerable } from '@baserow/modules/core/registry'

export class GroupSettingsPageType extends Registerable {
  /**
   * The name of the page in the tabs navigation at the top of the page.
   */
  getName() {
    return null
  }

  constructor(...args) {
    super(...args)
    this.type = this.getType()

    if (this.type === null) {
      throw new Error('The type name of a group settings page must be set.')
    }
  }

  serialize() {
    return {
      type: this.type,
      name: this.getName(),
    }
  }

  /**
   * Responsible for returning whether the user has access
   * to this group settings page type. By default, they do.
   */
  hasPermission(group) {
    return true
  }

  /**
   * Responsible for returning whether the user has access to
   * this page's features in this group.
   */
  isFeatureActive(group) {
    return true
  }

  getRoute() {
    throw new Error('The `getRoute` method must be set.')
  }
}

export class MembersGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'members'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('membersSettings.membersTabTitle')
  }

  getRoute(group) {
    return {
      name: 'settings-members',
      params: {
        groupId: group.id,
      },
    }
  }
}

export class InvitesGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'invites'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('membersSettings.invitesTabTitle')
  }

  /**
   * Responsible for returning whether the user has access to the
   * invitations table by checking their `group.list_invitations` permission.
   */
  hasPermission(group) {
    return this.app.$hasPermission('group.list_invitations', group, group.id)
  }

  getRoute(group) {
    return {
      name: 'settings-invites',
      params: {
        groupId: group.id,
      },
    }
  }
}
