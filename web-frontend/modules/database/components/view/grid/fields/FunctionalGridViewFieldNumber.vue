<template functional>
  <div
    class="grid-view__cell"
    :class="{
      ...(data.staticClass && {
        [data.staticClass]: true,
      }),
      'cell-error': props.value === 'NaN',
    }"
  >
    <div class="grid-field-number">
      {{ props.value !== 'NaN' ? props.value : 'Invalid Number' }}
    </div>
  </div>
</template>
