<template functional>
  <div
    v-if="props.value"
    class="array-field__single-select-option"
    :class="'background-color--' + props.value.color"
  >
    <div v-if="props.value.value" class="array-field__name">
      {{ props.value.value }}
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaSingleSelectArrayItem',
}
</script>
