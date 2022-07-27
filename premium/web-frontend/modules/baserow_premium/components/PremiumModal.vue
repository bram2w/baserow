<template>
  <Modal>
    <h2 class="box__title">
      {{ $t('premiumModal.title', { name }) }}
    </h2>
    <div>
      <p>
        {{ $t('premiumModal.description', { name }) }}
      </p>
      <PremiumFeatures class="margin-bottom-3"></PremiumFeatures>
      <a
        href="https://baserow.io/pricing"
        target="_blank"
        class="button button--primary button--large"
        >{{ $t('premiumModal.viewPricing') }}</a
      >
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import PremiumFeatures from '@baserow_premium/components/PremiumFeatures'

export default {
  name: 'PremiumModal',
  components: { PremiumFeatures },
  mixins: [modal],
  props: {
    name: {
      type: String,
      required: true,
    },
  },
}
</script>
