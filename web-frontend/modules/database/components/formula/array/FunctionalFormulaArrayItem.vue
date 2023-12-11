<template functional>
  <div v-if="props.value" class="array-field__item">
    <span>
      {{ props.value }}
    </span>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaArrayItem',
}
</script>
