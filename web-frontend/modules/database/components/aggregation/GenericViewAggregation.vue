<template functional>
  <div class="grid-view-aggregation__generic">
    <span class="grid-view-aggregation__generic-name">{{
      props.aggregationType.getShortName()
    }}</span>
    <span
      class="grid-view-aggregation__generic-value"
      :class="{
        'grid-view-aggregation__generic-value--loading': props.loading,
      }"
      >{{ props.value }}</span
    >
  </div>
</template>
