<template>
  <div class="auth-provider-admin__item">
    <AuthProviderIcon :icon="getIcon()" />
    <div class="auth-provider-admin__item-name">
      {{ getName() }}
    </div>
    <div class="auth-provider-admin__item-menu">
      <a ref="editMenuContextLink" @click="openContext()">
        <i class="fas fa-ellipsis-v"></i>
      </a>
      <EditAuthProviderMenuContext
        ref="editMenuContext"
        :auth-provider="authProvider"
        @edit="showUpdateSettingsModal"
        @delete="showDeleteModal"
      />
      <UpdateSettingsAuthProviderModal
        ref="updateSettingsModal"
        :auth-provider="authProvider"
        @settings-updated="onSettingsUpdated"
        @cancel="$refs.updateSettingsModal.hide()"
      />
      <DeleteAuthProviderModal
        ref="deleteModal"
        :auth-provider="authProvider"
        @deleteConfirmed="onDeleteConfirmed"
        @cancel="$refs.deleteModal.hide()"
      />
    </div>
    <SwitchInput
      class="auth-provider-admin__item-toggle"
      :value="authProvider.enabled"
      :large="true"
      @input="setEnabled($event)"
    ></SwitchInput>
  </div>
</template>

<script>
import SwitchInput from '@baserow/modules/core/components/SwitchInput.vue'
import EditAuthProviderMenuContext from '@baserow_enterprise/components/admin/contexts/EditAuthProviderMenuContext.vue'
import UpdateSettingsAuthProviderModal from '@baserow_enterprise/components/admin/modals/UpdateSettingsAuthProviderModal.vue'
import DeleteAuthProviderModal from '@baserow_enterprise/components/admin/modals/DeleteAuthProviderModal.vue'
import AuthProviderIcon from '@baserow_enterprise/components/AuthProviderIcon.vue'

export default {
  name: 'AuthProviderItem',
  components: {
    SwitchInput,
    DeleteAuthProviderModal,
    EditAuthProviderMenuContext,
    UpdateSettingsAuthProviderModal,
    AuthProviderIcon,
  },
  props: {
    authProvider: {
      type: Object,
      required: true,
    },
  },
  methods: {
    getIcon() {
      return this.$registry
        .get('authProvider', this.authProvider.type)
        .getIcon()
    },
    getName() {
      return this.$registry
        .get('authProvider', this.authProvider.type)
        .getProviderName(this.authProvider)
    },
    openContext() {
      this.$refs.editMenuContext.toggle(
        this.$refs.editMenuContextLink,
        'bottom',
        'right'
      )
    },
    showUpdateSettingsModal() {
      this.$refs.editMenuContext.hide()
      this.$refs.updateSettingsModal.show()
    },
    showDeleteModal() {
      this.$refs.deleteModal.show()
      this.$refs.editMenuContext.hide()
    },
    onDeleteConfirmed() {
      this.$store.dispatch('authProviderAdmin/delete', this.authProvider)
      this.$refs.deleteModal.hide()
    },
    onSettingsUpdated() {
      this.$refs.updateSettingsModal.hide()
    },
    async setEnabled(enabled) {
      await this.$store.dispatch('authProviderAdmin/setEnabled', {
        authProvider: this.authProvider,
        enabled,
      })
    },
  },
}
</script>
