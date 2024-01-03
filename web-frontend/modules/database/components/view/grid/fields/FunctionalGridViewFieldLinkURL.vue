<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-text">
      <a
        v-if="props.selected && $options.methods.isValid(props.value)"
        :href="props.value && props.value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ $options.methods.getLabelOrURL(props.value) }}
      </a>
      <u v-else-if="$options.methods.isValid(props.value)">
        {{ $options.methods.getLabelOrURL(props.value) }}
      </u>
      <span v-else>
        {{ $options.methods.getLabelOrURL(props.value) }}
      </span>
    </div>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'

export default {
  name: 'FunctionalGridViewFieldLinkURL',
  mixins: [linkURLField],
}
</script>
