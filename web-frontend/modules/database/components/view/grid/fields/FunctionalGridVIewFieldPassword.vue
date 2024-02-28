<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-password">
      <div class="grid-field-password__dots">
        {{ props.value ? '••••••••••' : '' }}
      </div>
    </div>
  </div>
</template>
