<template>
  <div class="formula-field__description">
    <div class="formula-field__description-heading-1">
      <i class="formula-field__description-icon" :class="[selectedItem.icon]" />
      {{ makeHeader(selectedItem.value) }}
    </div>
    <div class="formula-field__description-text">
      {{ selectedItem.description }}
    </div>
    <div class="formula-field__description-heading-2">
      {{ $t('formulaFieldItemDescription.syntax') }}
    </div>
    <pre
      v-for="usage in selectedItem.syntaxUsage"
      :key="usage.hashCode()"
      class="formula-field__description-example"
    ><code>{{ usage }}</code></pre>
    <div class="formula-field__description-heading-2">
      {{ $t('formulaFieldItemDescription.examples') }}
    </div>
    <pre
      v-for="example in selectedItem.examples"
      :key="example.hashCode()"
      class="formula-field__description-example"
    ><code>{{ example }}</code></pre>
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
  },
}
</script>
