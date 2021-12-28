<template functional>
  <div
    class="grid-view__cell"
    :class="{
      ...(data.staticClass && {
        [data.staticClass]: true,
      }),
    }"
  >
    <div class="grid-field-rating">
      <component
        :is="$options.components.Rating"
        :read-only="true"
        :rating-style="props.field.style"
        :color="props.field.color"
        :value="props.value"
        :max-value="props.field.max_value"
      ></component>
    </div>
  </div>
</template>

<script>
import Rating from '@baserow/modules/database/components/Rating'

export default {
  components: { Rating },
}
</script>
