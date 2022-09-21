<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div class="grid-field-text">
      <a
        v-if="props.selected && $options.methods.isValid(props.value)"
        :href="props.value && props.value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ $options.methods.getLabelOrUrl(props.value) }}
      </a>
      <u v-else-if="$options.methods.isValid(props.value)">
        {{ $options.methods.getLabelOrUrl(props.value) }}
      </u>
      <span v-else>
        {{ $options.methods.getLabelOrUrl(props.value) }}
      </span>
    </div>
  </div>
</template>

<script>
import { isValidURL } from '@baserow/modules/core/utils/string'
export default {
  name: 'FunctionalGridViewFieldLink',
  methods: {
    isValidURL,
    isValid(value) {
      return isValidURL(value?.url)
    },
    getLabelOrUrl(value) {
      if (!value) {
        return ''
      } else {
        return value.label ? value.label : value.url
      }
    },
  },
}
</script>
