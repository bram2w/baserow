import { registerRealtimeEvents } from '@baserow_enterprise/realtime'
import { RolePermissionManagerType } from '@baserow_enterprise/permissionManagerTypes'
import { AuthProvidersType } from '@baserow_enterprise/adminTypes'
import authProviderAdminStore from '@baserow_enterprise/store/authProviderAdmin'
import { PasswordAuthProviderType as CorePasswordAuthProviderType } from '@baserow/modules/core/authProviderTypes'
import {
  PasswordAuthProviderType,
  SamlAuthProviderType,
  GitHubAuthProviderType,
  GoogleAuthProviderType,
  FacebookAuthProviderType,
  GitLabAuthProviderType,
  OpenIdConnectAuthProviderType,
} from '@baserow_enterprise/authProviderTypes'

import { TeamsGroupSettingsPageType } from '@baserow_enterprise/groupSettingsPageTypes'
import { EnterpriseMembersPagePluginType } from '@baserow_enterprise/membersPagePluginTypes'
import en from '@baserow_enterprise/locales/en.json'
import fr from '@baserow_enterprise/locales/fr.json'
import nl from '@baserow_enterprise/locales/nl.json'
import de from '@baserow_enterprise/locales/de.json'
import es from '@baserow_enterprise/locales/es.json'
import it from '@baserow_enterprise/locales/it.json'
import {
  EnterpriseWithoutSupportLicenseType,
  EnterpriseLicenseType,
} from '@baserow_enterprise/licenseTypes'

import { EnterprisePlugin } from '@baserow_enterprise/plugins'

export default (context) => {
  const { app, isDev, store } = context

  // Allow locale file hot reloading
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
  }

  app.$registry.register('plugin', new EnterprisePlugin(context))

  app.$registry.register(
    'permissionManager',
    new RolePermissionManagerType(context)
  )

  store.registerModule('authProviderAdmin', authProviderAdminStore)

  app.$registry.register('admin', new AuthProvidersType(context))
  app.$registry.unregister(
    'authProvider',
    new CorePasswordAuthProviderType(context)
  )
  app.$registry.register('authProvider', new PasswordAuthProviderType(context))
  app.$registry.register('authProvider', new SamlAuthProviderType(context))
  app.$registry.register('authProvider', new GoogleAuthProviderType(context))
  app.$registry.register('authProvider', new FacebookAuthProviderType(context))
  app.$registry.register('authProvider', new GitHubAuthProviderType(context))
  app.$registry.register('authProvider', new GitLabAuthProviderType(context))
  app.$registry.register(
    'authProvider',
    new OpenIdConnectAuthProviderType(context)
  )
  app.$registry.register('plugin', new EnterprisePlugin(context))

  registerRealtimeEvents(app.$realtime)

  app.$registry.register(
    'membersPagePlugins',
    new EnterpriseMembersPagePluginType(context)
  )

  if (app.$featureFlagIsEnabled('RBAC')) {
    app.$registry.register(
      'groupSettingsPage',
      new TeamsGroupSettingsPageType(context)
    )
  }

  app.$registry.register(
    'license',
    new EnterpriseWithoutSupportLicenseType(context)
  )

  app.$registry.register('license', new EnterpriseLicenseType(context))
}
