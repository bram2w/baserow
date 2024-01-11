<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-button">
      <a
        v-if="$options.methods.isValid(props.value)"
        class="button button--tiny button--ghost"
        :href="props.value && props.value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ $options.methods.getLabelOrURL(props.value) }}
      </a>
      <a v-else class="button button--tiny button--ghost disabled">
        {{ $options.methods.getLabelOrURL(props.value) }}
      </a>
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
