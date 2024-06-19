<template functional>
  <div
    v-if="props.value"
    class="array-field__single-option"
    :class="'background-color--' + props.value.color"
  >
    <div class="array-field__ellipsis">{{ props.value.value }}</div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalFormulaSingleSelectArrayItem',
}
</script>
