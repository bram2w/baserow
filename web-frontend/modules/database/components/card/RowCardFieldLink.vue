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
      {{ $options.methods.getLabelOrUrl(props.value) }}
    </a>
    <template v-else>
      {{ $options.methods.getLabelOrUrl(props.value) }}
    </template>
  </div>
</template>

<script>
import { isValidURL } from '@baserow/modules/core/utils/string'
export default {
  name: 'RowCardFieldLink',
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
  height: 16,
}
</script>
