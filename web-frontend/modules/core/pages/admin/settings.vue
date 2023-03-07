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
          {{ $t('settings.accountRestrictions') }}
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
        <div v-if="!settings.allow_new_signups" class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingAllowSignupsViaGroupInvitationsName') }}
            </div>
            <div class="admin-settings__description">
              {{
                $t('settings.settingAllowSignupsViaGroupInvitationDescription')
              }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_signups_via_group_invitations"
              :large="true"
              @input="
                updateSettings({ allow_signups_via_group_invitations: $event })
              "
              >{{ $t('settings.enabled') }}</SwitchInput
            >
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingAllowResetPasswordName') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.settingAllowResetPasswordDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_reset_password"
              :large="true"
              @input="updateSettings({ allow_reset_password: $event })"
              >{{ $t('settings.enabled') }}</SwitchInput
            >
            <div v-show="!settings.allow_reset_password" class="warning">
              {{ $t('settings.settingAllowResetPasswordWarning') }}
            </div>
          </div>
        </div>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingAllowNonStaffCreateGroupOperation') }}
            </div>
            <div class="admin-settings__description">
              {{
                $t(
                  'settings.settingAllowNonStaffCreateGroupOperationDescription'
                )
              }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_global_group_creation"
              :large="true"
              @input="updateSettings({ allow_global_group_creation: $event })"
              >{{ $t('settings.enabled') }}</SwitchInput
            >
            <div v-show="settings.allow_global_group_creation" class="warning">
              {{
                $t('settings.settingAllowNonStaffCreateGroupOperationWarning')
              }}
            </div>
          </div>
        </div>
      </div>
      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">
          {{ $t('settings.userDeletionGraceDelay') }}
        </h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingUserDeletionGraceDelay') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.settingUserDeletionGraceDelayDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <input
              v-model="account_deletion_grace_delay"
              :class="{
                'input--error': $v.account_deletion_grace_delay.$error,
              }"
              type="number"
              class="input"
              @input="$v.account_deletion_grace_delay.$touch()"
            />
            <div v-if="$v.account_deletion_grace_delay.$error" class="error">
              {{ $t('settings.invalidAccountDeletionGraceDelay') }}
            </div>
          </div>
        </div>
      </div>
      <div class="admin-settings__group">
        <h2 class="admin-settings__group-title">
          {{ $t('settings.maintenance') }}
        </h2>
        <div class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{ $t('settings.settingTrackGroupUsage') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.settingTrackGroupUsageDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.track_group_usage"
              :large="true"
              @input="updateSettings({ track_group_usage: $event })"
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

import { required, integer, between } from 'vuelidate/lib/validators'

export default {
  layout: 'app',
  middleware: 'staff',
  async asyncData({ app }) {
    const { data } = await SettingsService(app.$client).getInstanceID()
    return { instanceId: data.instance_id }
  },
  data() {
    return { account_deletion_grace_delay: null }
  },
  computed: {
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  watch: {
    'settings.account_deletion_grace_delay'(value) {
      this.account_deletion_grace_delay = value
    },
    account_deletion_grace_delay(value) {
      this.updateSettings({ account_deletion_grace_delay: value })
    },
  },
  mounted() {
    this.account_deletion_grace_delay =
      this.settings.account_deletion_grace_delay
  },
  methods: {
    async updateSettings(values) {
      this.$v.$touch()
      if (this.$v.$invalid) {
        return
      }
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
  validations: {
    account_deletion_grace_delay: {
      required,
      between: between(0, 32000),
      integer: integer(),
    },
  },
}
</script>
