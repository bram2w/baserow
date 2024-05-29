<template>
  <div class="margin-top-1">
    <a v-if="hasPremium" @click="$refs.aiModal.show()">
      <i class="iconoir-magic-wand"></i>
      {{ $t('formulaFieldAI.generateWithAI') }}
    </a>
    <a v-else @click="$refs.premiumModal.show()">
      <i class="iconoir-lock"></i>
      {{ $t('formulaFieldAI.generateWithAI') }}
    </a>
    <AIFormulaModal
      ref="aiModal"
      :database="database"
      :table="table"
      @formula="$emit('update-formula', $event)"
    ></AIFormulaModal>
    <PremiumModal
      ref="premiumModal"
      :workspace="workspace"
      :name="$t('formulaFieldAI.featureName')"
    ></PremiumModal>
  </div>
</template>

<script>
import AIFormulaModal from '@baserow_premium/components/field/AIFormulaModal'
import PremiumFeatures from '@baserow_premium/features'
import PremiumModal from '@baserow_premium/components/PremiumModal.vue'

export default {
  name: 'FormulaFieldAI',
  components: { PremiumModal, AIFormulaModal },
  props: {
    database: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
  },
  computed: {
    hasPremium() {
      return this.$hasFeature(
        PremiumFeatures.PREMIUM,
        this.database.workspace.id
      )
    },
    workspace() {
      return this.$store.getters['workspace/get'](this.database.workspace.id)
    },
  },
}
</script>
