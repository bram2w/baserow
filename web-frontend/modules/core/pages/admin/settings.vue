<template>
  <div class="layout__col-2-scroll">
    <div class="admin-settings">
      <h1>Admin settings</h1>
      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">Signup restrictions</h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">Allow creating new accounts</div>
            <div class="admin-settings__description">
              By default, any user visiting your Baserow domain can sign up for
              a new account.
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_new_signups"
              :large="true"
              @input="updateSettings({ allow_new_signups: $event })"
              >enabled</SwitchInput
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

export default {
  layout: 'app',
  middleware: 'staff',
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
  },
}
</script>
