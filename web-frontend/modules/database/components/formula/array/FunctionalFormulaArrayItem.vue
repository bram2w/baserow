<template functional>
  <div v-if="props.value" class="array-field__item">
    <div class="array-field__ellipsis" :title="props.value">
      {{ props.value }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaArrayItem',
}
</script>
