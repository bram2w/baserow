<template>
  <div class="control__elements">
    <a
      v-if="isValidLinkURL"
      class="button button--tiny button--ghost"
      :href="copy && copy.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
    >
      {{ labelOrURL }}
    </a>
    <a v-else class="button button--tiny button--ghost disabled">
      {{ labelOrURL }}
    </a>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import linkURLField from '@baserow/modules/database/mixins/linkURLField'

export default {
  mixins: [rowEditField, rowEditFieldInput, linkURLField],
  computed: {
    isValidLinkURL() {
      return this.copy && this.isValid(this.copy)
    },
    labelOrURL() {
      return this.getLabelOrURL(this.copy)
    },
  },
}
</script>
