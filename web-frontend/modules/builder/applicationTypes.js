import { ApplicationType } from '@baserow/modules/core/applicationTypes'
import BuilderForm from '@baserow/modules/builder/components/form/BuilderForm'
import SidebarComponentBuilder from '@baserow/modules/builder/components/sidebar/SidebarComponentBuilder'

export class BuilderApplicationType extends ApplicationType {
  static getType() {
    return 'builder'
  }

  getIconClass() {
    return 'desktop'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('applicationType.builder')
  }

  getDefaultName() {
    const { i18n } = this.app
    return i18n.t('applicationType.builderDefaultName')
  }

  getApplicationFormComponent() {
    return BuilderForm
  }

  getSidebarComponent() {
    return SidebarComponentBuilder
  }
}
