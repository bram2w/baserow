<template functional>
  <div ref="cell" class="grid-view__cell">
    <div class="grid-field-single-select">
      <div
        v-if="props.value"
        class="grid-field-single-select__option"
        :class="'background-color--' + props.value.color"
      >
        {{ props.value.value }}
      </div>
    </div>
  </div>
</template>
