<template>
  <Modal>
    <component
      :is="contentComponent"
      v-if="contentComponent"
      :name="name"
      :workspace="workspace"
      @hide="hide"
    ></component>
    <template v-else>
      <h2 class="box__title">
        {{ $t('premiumModal.title', { name }) }}
      </h2>
      <div>
        <p>
          {{ $t('premiumModal.description', { name }) }}
        </p>
        <PremiumFeatures class="margin-bottom-3"></PremiumFeatures>
        <div>
          <Button
            type="primary"
            size="large"
            href="https://baserow.io/pricing"
            target="_blank"
            tag="a"
            >{{ $t('premiumModal.viewPricing') }}</Button
          >
        </div>
      </div>
    </template>
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
    workspace: {
      type: Object,
      required: true,
    },
  },
  computed: {
    contentComponent() {
      return this.$registry
        .get('plugin', 'premium')
        .getPremiumModalContentComponent()
    },
  },
}
</script>
