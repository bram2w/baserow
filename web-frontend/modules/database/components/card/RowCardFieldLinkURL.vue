<template functional>
  <div class="card-text">
    <a
      v-if="$options.methods.isValid(props.value)"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      class="forced-pointer-events-auto"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrURL(props.value) }}
    </a>
    <template v-else>
      {{ $options.methods.getLabelOrURL(props.value) }}
    </template>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'RowCardFieldLink',
  mixins: [linkURLField],
  height: 16,
}
</script>
