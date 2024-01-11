<template functional>
  <div class="card-button">
    <a
      v-if="$options.methods.isValid(props.value)"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      class="button button--tiny button--ghost forced-pointer-events-auto"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrURL(props.value) }}
    </a>
    <a v-else class="button button--tiny button--ghost disabled">
      {{ $options.methods.getLabelOrURL(props.value) }}
    </a>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'RowCardFieldButton',
  mixins: [linkURLField],
  height: 16,
}
</script>
