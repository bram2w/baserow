<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('registerLicenseModal.titleRegisterLicense') }}
    </h2>
    <div>
      <i18n path="registerLicenseModal.licenseDescription" tag="p">
        <template #pricingLink>
          <a target="_blank" href="https://baserow.io/pricing">{{
            $t('registerLicenseModal.viewPricing')
          }}</a>
        </template>
      </i18n>
      <p></p>
      <Error :error="error"></Error>
      <RegisterLicenseForm @submitted="submit">
        <div class="actions">
          <div class="align-right">
            <button
              class="button button--large"
              :class="{ 'button--loading': loading }"
              :disabled="loading"
            >
              {{ $t('registerLicenseModal.registerLicense') }}
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
            this.$t('registerLicenseModal.licenseError.invalidTitle'),
            this.$t('registerLicenseModal.licenseError.invalid')
          ),
          ERROR_UNSUPPORTED_PREMIUM_LICENSE: new ResponseErrorMessage(
            this.$t('registerLicenseModal.licenseError.unsupportedTitle'),
            this.$t('registerLicenseModal.licenseError.unsupported')
          ),
          ERROR_PREMIUM_LICENSE_HAS_EXPIRED: new ResponseErrorMessage(
            this.$t('registerLicenseModal.licenseError.expiredTitle'),
            this.$t('registerLicenseModal.licenseError.expired')
          ),
          ERROR_PREMIUM_LICENSE_ALREADY_EXISTS: new ResponseErrorMessage(
            this.$t('registerLicenseModal.licenseError.duplicateTitle'),
            this.$t('registerLicenseModal.licenseError.duplicate')
          ),
          ERROR_PREMIUM_LICENSE_INSTANCE_ID_MISMATCH: new ResponseErrorMessage(
            this.$t('registerLicenseModal.licenseError.instanceMismatchTitle'),
            this.$t('registerLicenseModal.licenseError.instanceMismatch')
          ),
        })
      }

      this.loading = false
    },
  },
}
</script>

<i18n>
{
  "en": {
    "registerLicenseModal": {
      "titleRegisterLicense": "Register a license",
      "registerLicense": "Register license",
      "viewPricing": "View pricing",
      "licenseDescription": "A license can only be obtained on baserow.io. If you have already purchased a license, it will be delivered to you by email and you can get in from the overview in your account. Copy and paste the license key in the box below and click on the button to register the license key to this instance. It’s not possible to use the same key on two different installations. {pricingLink} if you don’t have a key yet.",
      "licenseError": {
        "invalidTitle": "Invalid",
        "invalid": "The provided license is invalid.",
        "unsupportedTitle": "Unsupported",
        "unsupported": "The provided license is incompatible with your Baserow version. Please update to the latest version and try again.",
        "expiredTitle": "Expired",
        "expired": "The provided license has expired.",
        "duplicateTitle": "Duplicate",
        "duplicate": "The provided license is already registered to this instance.",
        "instanceMismatchTitle": "Instance mistmatch",
        "instanceMismatch": "The provided license does not belong to this instance."
      }
    }
  },
  "fr": {
    "registerLicenseModal": {
      "titleRegisterLicense": "Activer une licence",
      "registerLicense": "Activer la licence",
      "viewPricing": "Consultez les tarifs",
      "licenseDescription": "Une licence peut-être obtenue uniquement sur baserow.io. Si vous avez déjà acheté une licence, elle vous sera envoyée par email et vous pourrez la consulter dans votre compte. Copiez-collez la clé de licence dans le champ ci-dessous et cliquez sur le bouton afin d'activer la licence pour cette instance de Baserow. Il n'est pas possible d'utiliser la même clé pour plusieurs instances. {pricingLink} si vous n'avez pas encore de clé.",
      "licenseError": {
        "invalidTitle": "Invalide",
        "invalid": "La licence fournie est invalide.",
        "unsupportedTitle": "Non supportée",
        "unsupported": "La licence fournie est incompatible avec la version actuelle de Baserow. Veuillez mettre à jour votre instance avec la dernière version et essayez de nouveau.",
        "expiredTitle": "Expirée",
        "expired": "La licence fournie a expiré.",
        "duplicateTitle": "Déja enregistrée",
        "duplicate": "La licence fournie est déjà enregistrée sur cette instance.",
        "instanceMismatchTitle": "Instance incorrecte",
        "instanceMismatch": "La licence fournie n'a pas été créée pour cette instance."
      }
    }
  }
}
</i18n>
