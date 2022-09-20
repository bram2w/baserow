<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-text">
      <u>
        {{ props.value }}
      </u>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FunctionalGridViewFieldURL',
}
</script>
