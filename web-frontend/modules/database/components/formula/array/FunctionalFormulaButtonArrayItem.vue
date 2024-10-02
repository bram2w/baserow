<template functional>
  <div class="array-field__button">
    <Button
      v-if="$options.methods.isValid(props.value)"
      tag="a"
      size="tiny"
      type="secondary"
      class="forced-pointer-events-auto array-field__button-button"
      :href="props.value && props.value.url"
      target="_blank"
      rel="nofollow noopener noreferrer"
      @mousedown.stop
    >
      <span class=".array-field__ellipsis">{{
        $options.methods.getLabelOrURL(props.value)
      }}</span>
    </Button>
    <Button v-else size="tiny" type="secondary" tag="a" disabled>
      {{ $options.methods.getLabelOrURL(props.value) }}
    </Button>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'FunctionalFormulaButtonArrayItem',
  mixins: [linkURLField],
}
</script>
