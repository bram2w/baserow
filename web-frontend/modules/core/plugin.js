import Vue from 'vue'

import { Registry } from '@baserow/modules/core/registry'
import { PasswordAuthProviderType } from '@baserow/modules/core/authProviderTypes'
import {
  DuplicateApplicationJobType,
  InstallTemplateJobType,
} from '@baserow/modules/core/jobTypes'

import {
  AccountSettingsType,
  PasswordSettingsType,
  DeleteAccountSettingsType,
} from '@baserow/modules/core/settingsTypes'
import {
  UploadFileUserFileUploadType,
  UploadViaURLUserFileUploadType,
} from '@baserow/modules/core/userFileUploadTypes'
import { SettingsAdminType } from '@baserow/modules/core/adminTypes'

import {
  BasicPermissionManagerType,
  CorePermissionManagerType,
  StaffPermissionManagerType,
  GroupMemberPermissionManagerType,
} from '@baserow/modules/core/permissionManagerTypes'

import {
  MembersGroupSettingsPageType,
  InvitesGroupSettingsPageType,
} from '@baserow/modules/core/groupSettingsPageTypes'

import settingsStore from '@baserow/modules/core/store/settings'
import applicationStore from '@baserow/modules/core/store/application'
import authProviderStore from '@baserow/modules/core/store/authProvider'
import authStore from '@baserow/modules/core/store/auth'
import groupStore from '@baserow/modules/core/store/group'
import jobStore from '@baserow/modules/core/store/job'
import notificationStore from '@baserow/modules/core/store/notification'
import sidebarStore from '@baserow/modules/core/store/sidebar'
import undoRedoStore from '@baserow/modules/core/store/undoRedo'

import en from '@baserow/modules/core/locales/en.json'
import fr from '@baserow/modules/core/locales/fr.json'
import nl from '@baserow/modules/core/locales/nl.json'
import de from '@baserow/modules/core/locales/de.json'
import es from '@baserow/modules/core/locales/es.json'
import it from '@baserow/modules/core/locales/it.json'
import pl from '@baserow/modules/core/locales/pl.json'

export default (context, inject) => {
  const { store, isDev, app } = context
  inject('bus', new Vue())

  // Allow locale file hot reloading in dev
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
    i18n.mergeLocaleMessage('pl', pl)
  }

  const registry = new Registry()
  registry.registerNamespace('plugin')
  registry.registerNamespace('permissionManager')
  registry.registerNamespace('application')
  registry.registerNamespace('authProvider')
  registry.registerNamespace('job')
  registry.registerNamespace('view')
  registry.registerNamespace('field')
  registry.registerNamespace('settings')
  registry.registerNamespace('userFileUpload')
  registry.registerNamespace('membersPagePlugins')
  registry.register('settings', new AccountSettingsType(context))
  registry.register('settings', new PasswordSettingsType(context))
  registry.register('settings', new DeleteAccountSettingsType(context))
  registry.register('permissionManager', new CorePermissionManagerType(context))
  registry.register(
    'permissionManager',
    new StaffPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new GroupMemberPermissionManagerType(context)
  )
  registry.register(
    'permissionManager',
    new BasicPermissionManagerType(context)
  )
  registry.register('userFileUpload', new UploadFileUserFileUploadType(context))
  registry.register(
    'userFileUpload',
    new UploadViaURLUserFileUploadType(context)
  )
  registry.register('admin', new SettingsAdminType(context))
  inject('registry', registry)

  store.registerModule('settings', settingsStore)
  store.registerModule('application', applicationStore)
  store.registerModule('authProvider', authProviderStore)
  store.registerModule('auth', authStore)
  store.registerModule('job', jobStore)
  store.registerModule('group', groupStore)
  store.registerModule('notification', notificationStore)
  store.registerModule('sidebar', sidebarStore)
  store.registerModule('undoRedo', undoRedoStore)

  registry.register('authProvider', new PasswordAuthProviderType(context))
  registry.register('job', new DuplicateApplicationJobType(context))
  registry.register('job', new InstallTemplateJobType(context))

  registry.register(
    'groupSettingsPage',
    new MembersGroupSettingsPageType(context)
  )
  registry.register(
    'groupSettingsPage',
    new InvitesGroupSettingsPageType(context)
  )
}
