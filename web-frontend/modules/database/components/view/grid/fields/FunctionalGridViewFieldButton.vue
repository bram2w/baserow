<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-button">
      <Button
        v-if="$options.methods.isValid(props.value)"
        tag="a"
        type="secondary"
        size="tiny"
        :href="props.value && props.value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ $options.methods.getLabelOrURL(props.value) }}
      </Button>
      <Button v-else tag="a" type="secondary" size="tiny" disabled>
        {{ $options.methods.getLabelOrURL(props.value) }}
      </Button>
    </div>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'

export default {
  name: 'FunctionalGridViewFieldButton',
  mixins: [linkURLField],
}
</script>
