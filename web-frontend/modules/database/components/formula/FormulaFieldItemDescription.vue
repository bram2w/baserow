<template>
  <div class="formula-field__description">
    <div class="formula-field__description-heading-1">
      <i
        class="fas formula-field__description-icon"
        :class="[selectedItem.icon]"
      />
      {{ makeHeader(selectedItem.value) }}
    </div>
    <div class="formula-field__description-text">
      {{ selectedItem.description }}
    </div>
    <div class="formula-field__description-heading-2">Syntax</div>
    <pre
      class="formula-field__description-example"
    ><code>{{ formatList(selectedItem.syntaxUsage) }}</code></pre>
    <div class="formula-field__description-heading-2">Examples</div>
    <pre
      class="formula-field__description-example"
    ><code>{{ formatList(selectedItem.examples) }}</code></pre>
  </div>
</template>
<script>
export default {
  name: 'FormulaFieldItemDescription',
  props: {
    selectedItem: {
      type: Object,
      required: true,
    },
  },
  methods: {
    makeHeader(header) {
      return header.replaceAll('_', ' ')
    },
    formatList(item) {
      if (Array.isArray(item)) {
        return item.join('\n')
      } else {
        return item
      }
    },
  },
}
</script>
