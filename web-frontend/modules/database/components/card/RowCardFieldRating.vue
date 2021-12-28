<template functional>
  <component
    :is="$options.components.Rating"
    :read-only="true"
    :rating-style="props.field.style"
    :color="props.field.color"
    :value="props.value"
    :max-value="props.field.max_value"
    class="card-rating"
  ></component>
</template>

<script>
import Rating from '@baserow/modules/database/components/Rating'

export default {
  height: 18,
  components: { Rating },
}
</script>
