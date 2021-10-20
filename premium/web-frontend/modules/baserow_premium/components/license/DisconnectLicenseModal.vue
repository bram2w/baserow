<template>
  <Modal>
    <h2 class="box__title">Disconnect license</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure that you want to disconnect this license? If the license is
        active, all the users that have a seat will lose access. It will
        effectively be removed. Please contact our support team at
        <a href="https://baserow.io/contact" target="_blank"
          >baserow.io/contact</a
        >
        if you want to use this license in another self hosted instance.
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="disconnectLicense()"
          >
            Disconnect license
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
