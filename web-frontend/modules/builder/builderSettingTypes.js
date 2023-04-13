import { Registerable } from '@baserow/modules/core/registry'
import IntegrationSettings from '@baserow/modules/builder/components/settings/IntegrationSettings'
import ThemeSettings from '@baserow/modules/builder/components/settings/ThemeSettings'
import DomainsSettings from '@baserow/modules/builder/components/settings/DomainsSettings'

class BuilderSettingType extends Registerable {
  getType() {
    return null
  }

  get name() {
    return null
  }

  get icon() {
    return null
  }

  get component() {
    return null
  }
}

export class IntegrationsBuilderSettingsType extends BuilderSettingType {
  getType() {
    return 'integrations'
  }

  get name() {
    return this.app.i18n.t('builderSettingTypes.integrationsName')
  }

  get icon() {
    return 'plug'
  }

  getOrder() {
    return 10
  }

  get component() {
    return IntegrationSettings
  }
}

export class ThemeBuilderSettingsType extends BuilderSettingType {
  getType() {
    return 'theme'
  }

  get name() {
    return this.app.i18n.t('builderSettingTypes.themeName')
  }

  get icon() {
    return 'tint'
  }

  getOrder() {
    return 20
  }

  get component() {
    return ThemeSettings
  }
}

export class DomainsBuilderSettingsType extends BuilderSettingType {
  getType() {
    return 'domains'
  }

  get name() {
    return this.app.i18n.t('builderSettingTypes.domainsName')
  }

  get icon() {
    return 'globe'
  }

  getOrder() {
    return 5
  }

  get component() {
    return DomainsSettings
  }
}
