<template>
  <Modal>
    <h2 class="box__title">Register a license</h2>
    <div>
      <p>
        A license can only be obtained on baserow.io. If you have already
        purchased a license, it will be delivered to you by email and you can
        get in from the overview in your account. Copy and paste the license key
        in the box below and click on the button to register the license key to
        this instance. It’s not possible to use the same key on two different
        installations.
        <a target="_blank" href="https://baserow.io/pricing">View pricing</a> if
        you don’t have a key yet.
      </p>
      <Error :error="error"></Error>
      <RegisterLicenseForm @submitted="submit">
        <div class="actions">
          <div class="align-right">
            <button
              class="button button--large"
              :class="{ 'button--loading': loading }"
              :disabled="loading"
            >
              Register license
            </button>
          </div>
        </div>
      </RegisterLicenseForm>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import LicenseService from '@baserow_premium/services/license'
import RegisterLicenseForm from '@baserow_premium/components/license/RegisterLicenseForm'
import { ResponseErrorMessage } from '@baserow/modules/core/plugins/clientHandler'

export default {
  name: 'RegisterLicenseModal',
  components: { RegisterLicenseForm },
  mixins: [modal, error],
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async submit(values) {
      this.hideError()
      this.loading = true

      try {
        const { data } = await LicenseService(this.$client).register(
          values.license
        )
        this.$emit('registered', data)
        await this.$nuxt.$router.push({
          name: 'admin-license',
          params: {
            id: data.id,
          },
        })
      } catch (error) {
        this.handleError(error, 'license', {
          ERROR_INVALID_PREMIUM_LICENSE: new ResponseErrorMessage(
            'Invalid',
            'The provided license is invalid.'
          ),
          ERROR_UNSUPPORTED_PREMIUM_LICENSE: new ResponseErrorMessage(
            'Unsupported',
            'The provided license is incompatible with your Baserow version. Please update to the latest version and try again.'
          ),
          ERROR_PREMIUM_LICENSE_HAS_EXPIRED: new ResponseErrorMessage(
            'Expired',
            'The provided license has expired.'
          ),
          ERROR_PREMIUM_LICENSE_ALREADY_EXISTS: new ResponseErrorMessage(
            'Duplicate',
            'The provided license is already registered to this instance.'
          ),
          ERROR_PREMIUM_LICENSE_INSTANCE_ID_MISMATCH: new ResponseErrorMessage(
            'Instance mismatch',
            'The provided license does not belong to this instance.'
          ),
        })
      }

      this.loading = false
    },
  },
}
</script>
