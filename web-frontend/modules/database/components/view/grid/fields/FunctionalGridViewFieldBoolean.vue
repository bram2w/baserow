<template functional>
  <div class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-boolean">
      <div
        class="grid-field-boolean__checkbox"
        :class="{ active: props.value }"
      >
        <i class="iconoir-check grid-field-boolean__checkbox-icon"></i>
      </div>
    </div>
  </div>
</template>
