<template functional>
  <div class="array-field__item array-field__item--button">
    <Button
      v-if="$options.methods.isValid(props.value)"
      size="tiny"
      type="secondary"
      class="forced-pointer-events-auto"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      @mousedown.stop
    >
      {{ $options.methods.getLabelOrURL(props.value) }}
    </Button>
    <Button v-else size="tiny" type="secondary" disabled>
      {{ $options.methods.getLabelOrURL(props.value) }}
    </Button>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'FunctionalFormulaLinkArrayItem',
  mixins: [linkURLField],
}
</script>
