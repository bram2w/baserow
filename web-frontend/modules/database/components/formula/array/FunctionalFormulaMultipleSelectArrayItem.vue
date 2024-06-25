<template functional>
  <span class="array-field__multiple-select-container">
    <div
      v-for="item in props.value"
      :key="item.id"
      class="array-field__single-option"
      :class="'background-color--' + item.color"
    >
      <div class="array-field__ellipsis">{{ item.value }}</div>
    </div>
  </span>
</template>

<script>
export default {
  name: 'FunctionalFormulaMultipleSelectArrayItem',
}
</script>
