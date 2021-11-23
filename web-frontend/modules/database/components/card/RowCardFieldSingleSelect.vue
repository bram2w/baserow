<template functional>
  <div class="card-single-select-option__wrapper">
    <div
      v-if="props.value"
      class="card-single-select-option"
      :class="'background-color--' + props.value.color"
    >
      {{ props.value.value }}
    </div>
  </div>
</template>

<script>
export default {
  height: 20,
}
</script>
