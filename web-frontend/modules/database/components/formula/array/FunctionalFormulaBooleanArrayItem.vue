<template functional>
  <div class="array-field__boolean">
    <div class="array-field__checkbox">
      <i v-if="props.value" class="fas fa-check"></i>
      <i v-else class="fas fa-times array-field__checkbox--false"></i>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaBooleanArrayItem',
}
</script>
