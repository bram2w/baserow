<template>
  <div
    v-tooltip="tooltipText"
    class="view-sharing__option"
    :class="{ 'view-sharing__option--disabled': !hasPremiumFeatures }"
    @click="click"
  >
    <SwitchInput
      small
      :value="!view.show_logo"
      :disabled="!hasPremiumFeatures"
      @input="update"
    >
      <img src="@baserow/modules/core/static/img/baserow-icon.svg" />
      <span>
        {{ $t('shareLinkOptions.baserowLogo.label') }}
      </span>
      <i v-if="!hasPremiumFeatures" class="deactivated-label iconoir-lock" />
    </SwitchInput>

    <PremiumModal
      v-if="!hasPremiumFeatures"
      ref="premiumModal"
      :workspace="workspace"
      :name="$t('shareLinkOptions.baserowLogo.premiumModalName')"
    ></PremiumModal>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import ViewPremiumService from '@baserow_premium/services/view'
import { notifyIf } from '@baserow/modules/core/utils/error'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import PremiumFeatures from '@baserow_premium/features'

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
    workspace() {
      return this.$store.getters['application/get'](this.view.table.database_id)
        .workspace
    },
    hasPremiumFeatures() {
      return this.$hasFeature(PremiumFeatures.PREMIUM, this.workspace.id)
    },
    tooltipText() {
      if (this.hasPremiumFeatures) {
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
      if (!this.hasPremiumFeatures) {
        this.$refs.premiumModal.show()
      }
    },
  },
}
</script>
