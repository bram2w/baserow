<template>
  <div ref="cell" class="grid-view__cell">
    <div class="grid-field-button">
      <a
        v-if="isValid(value)"
        class="button button--tiny button--ghost"
        :href="value && value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
      >
        {{ getLabelOrURL(value) }}
      </a>
      <a v-else class="button button--tiny button--ghost disabled">
        {{ getLabelOrURL(value) }}
      </a>
    </div>
  </div>
</template>

<script>
import gridField from '@baserow/modules/database/mixins/gridField'
import gridFieldInput from '@baserow/modules/database/mixins/gridFieldInput'
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'GridViewFieldButton',
  mixins: [gridField, gridFieldInput, linkURLField],
}
</script>
