<template>
  <div class="control__elements">
    <a
      v-if="isValidLinkURL"
      :href="copy && copy.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
    >
      {{ labelOrURL }}
    </a>
    <span v-else>
      {{ labelOrURL }}
    </span>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import { isValidURL } from '@baserow/modules/core/utils/string'

export default {
  mixins: [rowEditField, rowEditFieldInput],
  computed: {
    isValidLinkURL() {
      return this.copy && isValidURL(this.copy.url)
    },
    labelOrURL() {
      if (!this.copy) {
        return ''
      } else {
        return this.copy.label ? this.copy.label : this.copy.url
      }
    },
  },
}
</script>
