<template functional>
  <div>
    <Button
      v-if="$options.methods.isValid(props.value)"
      :href="props.value && props.value.url"
      tag="a"
      target="_blank"
      rel="nofollow noopener noreferrer"
      size="tiny"
      type="secondary"
      class="forced-pointer-events-auto"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrURL(props.value) }}
    </Button>
    <Button v-else tag="a" type="secondary" size="tiny" disabled>
      {{ $options.methods.getLabelOrURL(props.value) }}
    </Button>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'RowCardFieldButton',
  mixins: [linkURLField],
  height: 26,
}
</script>
