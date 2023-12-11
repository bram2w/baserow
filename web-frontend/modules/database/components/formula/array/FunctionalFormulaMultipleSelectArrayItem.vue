<template functional>
  <div class="array-field__multiple-select-item">
    <div
      v-for="item in props.value"
      :key="item.id"
      class="array-field__multiple-select-option"
      :class="'background-color--' + item.color"
    >
      <div v-if="item.value" class="array-field__name">
        {{ item.value }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaMultipleSelectArrayItem',
}
</script>
