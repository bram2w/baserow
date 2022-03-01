<template functional>
  <div class="grid-view-aggregation__generic">
    <span class="grid-view-aggregation__generic__name">{{
      props.aggregationType.getShortName()
    }}</span>
    <span
      class="grid-view-aggregation__generic__value"
      :class="{
        'grid-view-aggregation__generic__value--loading': props.loading,
      }"
      >{{ props.value }}</span
    >
  </div>
</template>
