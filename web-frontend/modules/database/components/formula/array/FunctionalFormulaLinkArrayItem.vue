<template functional>
  <div class="array-field__item">
    <a
      v-if="props.selected && $options.methods.isValid(props.value)"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      class="forced-pointer-events-auto"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrUrl(props.value) }}
    </a>
    <u v-else-if="$options.methods.isValid(props.value)">
      {{ $options.methods.getLabelOrUrl(props.value) }}
    </u>
    <template v-else>
      {{ $options.methods.getLabelOrUrl(props.value) }}
    </template>
  </div>
</template>

<script>
import { isValidURL } from '@baserow/modules/core/utils/string'
export default {
  name: 'FunctionalFormulaLinkArrayItem',
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
