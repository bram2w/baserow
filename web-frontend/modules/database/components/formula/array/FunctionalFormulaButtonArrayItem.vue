<template functional>
  <div class="array-field__item array-field__item--button">
    <a
      v-if="$options.methods.isValid(props.value)"
      class="button button--tiny button--ghost forced-pointer-events-auto"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrURL(props.value) }}
    </a>
    <a v-else class="button button--tiny button--ghost disabled">
      {{ $options.methods.getLabelOrURL(props.value) }}
    </a>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'FunctionalFormulaLinkArrayItem',
  mixins: [linkURLField],
}
</script>
