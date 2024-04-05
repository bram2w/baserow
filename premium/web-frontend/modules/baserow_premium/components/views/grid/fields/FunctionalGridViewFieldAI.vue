<template functional>
  <div
    v-if="!props.value || $options.methods.isGenerating(parent, props)"
    class="grid-view__cell"
  >
    <div class="grid-field-button">
      <a
        class="button button--tiny button--ghost"
        :disabled="!$options.methods.isModelAvailable(parent, props)"
        :class="{
          'button--loading': $options.methods.isGenerating(parent, props),
        }"
      >
        <i18n path="functionalGridViewFieldAI.generate" tag="span" />
      </a>
    </div>
  </div>
  <div v-else class="grid-view__cell grid-field-long-text__cell">
    <div class="grid-field-long-text">{{ props.value }}</div>
  </div>
</template>

<script>
import gridFieldAI from '@baserow_premium/mixins/gridFieldAI'

export default {
  name: 'FunctionalGridViewFieldAI',
  mixins: [gridFieldAI],
}
</script>
