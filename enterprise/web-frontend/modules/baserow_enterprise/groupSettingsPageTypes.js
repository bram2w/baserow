import { GroupSettingsPageType } from '@baserow/modules/core/groupSettingsPageTypes'
import EnterpriseFeatures from '@baserow_enterprise/features'

export class TeamsGroupSettingsPageType extends GroupSettingsPageType {
  getType() {
    return 'teams'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('teamsSettings.teamsTabTitle')
  }

  /**
   * Responsible for returning whether the user has access to the
   * teams table by checking their `enterprise.teams.list_teams` permission.
   */
  hasPermission(group) {
    return this.app.$hasPermission(
      'enterprise.teams.list_teams',
      group,
      group.id
    )
  }

  /**
   * Responsible for returning whether the user has access to
   * the teams role-based access control feature.
   */
  isFeatureActive(group) {
    return this.app.$hasFeature(EnterpriseFeatures.TEAMS, group.id)
  }

  getRoute(group) {
    return {
      name: 'settings-teams',
      params: {
        groupId: group.id,
      },
    }
  }
}
