<template functional>
  <div
    v-if="
      (!props.value || $options.methods.isGenerating(parent, props)) &&
      !props.readOnly
    "
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
        <i
          v-if="$options.methods.isDeactivatedFunctional(parent, props)"
          class="iconoir-lock"
        ></i>
      </a>
    </div>
  </div>
  <div v-else class="grid-view__cell grid-field-long-text__cell">
    <div class="grid-field-long-text">{{ props.value }}</div>
  </div>
</template>

<script>
import gridFieldAI from '@baserow_premium/mixins/gridFieldAI'
import { AIFieldType } from '@baserow_premium/fieldTypes'

export default {
  name: 'FunctionalGridViewFieldAI',
  mixins: [gridFieldAI],
  methods: {
    isDeactivatedFunctional(parent, props) {
      return parent.$registry
        .get('field', AIFieldType.getType())
        .isDeactivated(props.workspaceId)
    },
  },
}
</script>
