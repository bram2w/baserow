<template>
  <div ref="cell" class="grid-view__cell">
    <div class="grid-field-text">
      <a
        v-if="selected && isValid(value)"
        :href="value && value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ getLabelOrUrl(value) }}
      </a>
      <u v-else-if="isValid(value)">
        {{ getLabelOrUrl(value) }}
      </u>
      <span v-else>
        {{ getLabelOrUrl(value) }}
      </span>
    </div>
  </div>
</template>

<script>
import { isValidURL } from '@baserow/modules/core/utils/string'
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'
export default {
  name: 'GridViewFieldLinkURL',
  mixins: [gridField, gridFieldInput],
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
