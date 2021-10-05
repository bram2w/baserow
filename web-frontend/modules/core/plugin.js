import Vue from 'vue'

import { Registry } from '@baserow/modules/core/registry'

import { PasswordSettingsType } from '@baserow/modules/core/settingsTypes'
import {
  UploadFileUserFileUploadType,
  UploadViaURLUserFileUploadType,
} from '@baserow/modules/core/userFileUploadTypes'
import { SettingsAdminType } from '@baserow/modules/core/adminTypes'

import settingsStore from '@baserow/modules/core/store/settings'
import applicationStore from '@baserow/modules/core/store/application'
import authStore from '@baserow/modules/core/store/auth'
import groupStore from '@baserow/modules/core/store/group'
import notificationStore from '@baserow/modules/core/store/notification'
import sidebarStore from '@baserow/modules/core/store/sidebar'

export default (context, inject) => {
  const { store } = context
  inject('bus', new Vue())

  const registry = new Registry()
  registry.registerNamespace('plugin')
  registry.registerNamespace('application')
  registry.registerNamespace('view')
  registry.registerNamespace('field')
  registry.registerNamespace('settings')
  registry.registerNamespace('userFileUpload')
  registry.register('settings', new PasswordSettingsType(context))
  registry.register('userFileUpload', new UploadFileUserFileUploadType(context))
  registry.register(
    'userFileUpload',
    new UploadViaURLUserFileUploadType(context)
  )
  registry.register('admin', new SettingsAdminType(context))
  inject('registry', registry)

  store.registerModule('settings', settingsStore)
  store.registerModule('application', applicationStore)
  store.registerModule('auth', authStore)
  store.registerModule('group', groupStore)
  store.registerModule('notification', notificationStore)
  store.registerModule('sidebar', sidebarStore)
}
