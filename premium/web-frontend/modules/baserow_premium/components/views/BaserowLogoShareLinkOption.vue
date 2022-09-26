<template>
  <div
    class="view-sharing__option"
    :class="{ 'view-sharing__option--disabled': !validPremiumLicense }"
    @click="click"
  >
    <SwitchInput
      large
      :value="!view.show_logo"
      :disabled="!validPremiumLicense"
      @input="update"
    ></SwitchInput>
    <div v-tooltip="tooltipText" class="margin-left-2">
      <img
        src="@baserow/modules/core/static/img/baserow-icon.svg"
        class="margin-right-1"
      />
      <span>
        {{ $t('shareLinkOptions.baserowLogo.label') }}
      </span>
      <i v-if="!validPremiumLicense" class="deactivated-label fas fa-lock"></i>
    </div>
    <PremiumModal
      v-if="!validPremiumLicense"
      ref="premiumModal"
      :name="$t('shareLinkOptions.baserowLogo.premiumModalName')"
    ></PremiumModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ViewPremiumService from '@baserow_premium/services/view'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { PremiumPlugin } from '@baserow_premium/plugins'
import PremiumModal from '@baserow_premium/components/PremiumModal'

export default {
  name: 'BaserowLogoShareLinkOption',
  components: { PremiumModal },

  props: {
    view: {
      type: Object,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      additionalUserData: 'auth/getAdditionalUserData',
    }),
    group() {
      return this.$store.getters['application/get'](this.view.table.database_id)
        .group
    },
    validPremiumLicense() {
      return PremiumPlugin.hasValidPremiumLicense(
        this.additionalUserData,
        this.group.id
      )
    },
    tooltipText() {
      if (this.validPremiumLicense) {
        return null
      } else {
        return this.$t('premium.deactivated')
      }
    },
  },
  methods: {
    async update(value) {
      const showLogo = !value
      try {
        // We are being optimistic that the request will succeed.
        this.$emit('update-view', { ...this.view, show_logo: showLogo })
        await ViewPremiumService(this.$client).update(this.view.id, {
          show_logo: showLogo,
        })
      } catch (error) {
        // In case it didn't we will roll back the change.
        this.$emit('update-view', { ...this.view, show_logo: !showLogo })
        notifyIf(error, 'view')
      }
    },
    click() {
      if (!this.validPremiumLicense) {
        this.$refs.premiumModal.show()
      }
    },
  },
}
</script>
