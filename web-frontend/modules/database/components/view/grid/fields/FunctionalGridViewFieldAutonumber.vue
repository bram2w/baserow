<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-number">{{ props.value }}</div>
  </div>
</template>
