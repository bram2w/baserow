<template>
  <div class="layout__col-2-scroll">
    <div class="admin-settings">
      <h1>{{ $t('settings.settingsTitle') }}</h1>
      <div class="admin-settings__group">
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.baserowInstanceId') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.instanceIdDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            {{ instanceId }}
            <a
              class="licenses__instance-id-copy"
              @click.prevent="
                ;[copyToClipboard(instanceId), $refs.instanceIdCopied.show()]
              "
            >
              {{ $t('action.copy') }}
              <Copied ref="instanceIdCopied"></Copied>
            </a>
          </div>
        </div>
      </div>
      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">
          {{ $t('settings.groupSignupRestrictions') }}
        </h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingAllowNewAccountsName') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.settingAllowNewAccountsDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_new_signups"
              :large="true"
              @input="updateSettings({ allow_new_signups: $event })"
              >{{ $t('settings.enabled') }}</SwitchInput
            >
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

import { notifyIf } from '@baserow/modules/core/utils/error'
import SettingsService from '@baserow/modules/core/services/settings'
import { copyToClipboard } from '@baserow/modules/database/utils/clipboard'

export default {
  layout: 'app',
  middleware: 'staff',
  async asyncData({ app }) {
    const { data } = await SettingsService(app.$client).getInstanceID()
    return { instanceId: data.instance_id }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  methods: {
    async updateSettings(values) {
      try {
        await this.$store.dispatch('settings/update', values)
      } catch (error) {
        notifyIf(error, 'settings')
      }
    },
    copyToClipboard(value) {
      copyToClipboard(value)
    },
  },
}
</script>
