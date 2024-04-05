import {
  AdminRoleType,
  MemberRoleType,
} from '@baserow/modules/database/roleTypes'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import EnterpriseFeatures from '@baserow_enterprise/features'

export class EnterpriseAdminRoleType extends AdminRoleType {
  showIsBillable(workspaceId) {
    return this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getIsBillable(workspaceId) {
    return this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }
}

export class EnterpriseMemberRoleType extends MemberRoleType {
  // This role doesn't exist in enterprise, so we hide it completely.
  isVisible(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }
}

export class EnterpriseBuilderRoleType extends MemberRoleType {
  getType() {
    return 'builder'
  }

  getUid() {
    return 'BUILDER'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.builder.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.builder.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return true
  }

  isVisible(workspaceId) {
    return this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }
}

export class EnterpriseEditorRoleType extends MemberRoleType {
  getType() {
    return 'editor'
  }

  getUid() {
    return 'EDITOR'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.editor.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.editor.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return true
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}

export class EnterpriseCommenterRoleType extends MemberRoleType {
  getType() {
    return 'commenter'
  }

  getUid() {
    return 'COMMENTER'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.commenter.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.commenter.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return false
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}

export class EnterpriseViewerRoleType extends MemberRoleType {
  getType() {
    return 'viewer'
  }

  getUid() {
    return 'VIEWER'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.viewer.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.viewer.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return false
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}

export class NoAccessRoleType extends MemberRoleType {
  getType() {
    return 'noAccess'
  }

  getUid() {
    return 'NO_ACCESS'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.noAccess.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.noAccess.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return false
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}

export class NoRoleLowPriorityRoleType extends MemberRoleType {
  getType() {
    return 'noRoleLowPriority'
  }

  getUid() {
    return 'NO_ROLE_LOW_PRIORITY'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('roles.noRoleLowPriority.name')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('roles.noRoleLowPriority.description')
  }

  showIsBillable(workspaceId) {
    return true
  }

  getIsBillable(workspaceId) {
    return false
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(EnterpriseFeatures.RBAC, workspaceId)
  }

  getDeactivatedClickModal(workspaceId) {
    return PremiumModal
  }
}
