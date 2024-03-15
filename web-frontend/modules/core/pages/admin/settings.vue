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
              @input="updateSettings({ allow_new_signups: $event })"
              >{{ $t('settings.enabled') }}</SwitchInput
            >
          </div>
        </div>
        <div v-if="!settings.allow_new_signups" class="admin-settings__item">
          <div class="admin-settings__label">
            <div class="admin-settings__name">
              {{
                $t('settings.settingAllowSignupsViaWorkspaceInvitationsName')
              }}
            </div>
            <div class="admin-settings__description">
              {{
                $t(
                  'settings.settingAllowSignupsViaWorkspaceInvitationDescription'
                )
              }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_signups_via_workspace_invitations"
              @input="
                updateSettings({
                  allow_signups_via_workspace_invitations: $event,
                })
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
              {{ $t('settings.settingAllowNonStaffCreateWorkspaceOperation') }}
            </div>
            <div class="admin-settings__description">
              {{
                $t(
                  'settings.settingAllowNonStaffCreateWorkspaceOperationDescription'
                )
              }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.allow_global_workspace_creation"
              @input="
                updateSettings({ allow_global_workspace_creation: $event })
              "
              >{{ $t('settings.enabled') }}</SwitchInput
            >
            <div
              v-show="settings.allow_global_workspace_creation"
              class="warning"
            >
              {{
                $t(
                  'settings.settingAllowNonStaffCreateWorkspaceOperationWarning'
                )
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
              @input="
                ;[
                  $v.account_deletion_grace_delay.$touch(),
                  updateAccountDeletionGraceDelay($event),
                ]
              "
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
              {{ $t('settings.settingTrackWorkspaceUsage') }}
            </div>
            <div class="admin-settings__description">
              {{ $t('settings.settingTrackWorkspaceUsageDescription') }}
            </div>
          </div>
          <div class="admin-settings__control">
            <SwitchInput
              :value="settings.track_workspace_usage"
              @input="updateSettings({ track_workspace_usage: $event })"
              >{{ $t('settings.enabled') }}</SwitchInput
            >
          </div>
        </div>
      </div>
      <component
        :is="component"
        v-for="(component, index) in additionalSettingsComponents"
        :key="index"
      ></component>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { required, integer, between } from 'vuelidate/lib/validators'

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
  data() {
    return { account_deletion_grace_delay: null }
  },
  computed: {
    additionalSettingsComponents() {
      return Object.values(this.$registry.getAll('plugin'))
        .reduce(
          (components, plugin) =>
            components.concat(plugin.getSettingsPageComponents()),
          []
        )
        .filter((component) => component !== null)
    },
    ...mapGetters({
      settings: 'settings/get',
    }),
  },
  watch: {
    'settings.account_deletion_grace_delay'(value) {
      this.account_deletion_grace_delay = value
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
    updateAccountDeletionGraceDelay() {
      const existingValue = this.settings.account_deletion_grace_delay

      if (
        !this.$v.account_deletion_grace_delay.$error &&
        existingValue !== parseInt(this.account_deletion_grace_delay)
      ) {
        this.updateSettings({
          account_deletion_grace_delay: parseInt(
            this.account_deletion_grace_delay
          ),
        })
      }
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
