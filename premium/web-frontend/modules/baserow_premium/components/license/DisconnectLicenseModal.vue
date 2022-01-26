<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('disconnectLicenseModal.disconnectLicense') }}
    </h2>
    <Error :error="error"></Error>
    <div>
      <i18n path="disconnectLicenseModal.disconnectDescription" tag="p">
        <template #contact>
          <a href="https://baserow.io/contact" target="_blank"
            >baserow.io/contact</a
          >
        </template>
      </i18n>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="disconnectLicense()"
          >
            {{ $t('disconnectLicenseModal.disconnectLicense') }}
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import LicenseService from '@baserow_premium/services/license'

export default {
  name: 'DisconnectLicenseModal',
  mixins: [modal, error],
  props: {
    license: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async disconnectLicense() {
      this.hideError()
      this.loading = true

      try {
        await LicenseService(this.$client).disconnect(this.license.id)
        await this.$nuxt.$router.push({ name: 'admin-licenses' })
      } catch (error) {
        this.handleError(error)
      }

      this.loading = false
    },
  },
}
</script>
