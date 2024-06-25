<template functional>
  <div class="array-field__item">
    <div class="array-field__ellipsis">
      <a
        v-if="props.selected && $options.methods.isValid(props.value)"
        :href="props.value && props.value.url"
        target="_blank"
        rel="nofollow noopener noreferrer"
        class="forced-pointer-events-auto"
        @mousedown.stop
      >
        {{ $options.methods.getLabelOrURL(props.value) }}
      </a>
      <u v-else-if="$options.methods.isValid(props.value)">
        {{ $options.methods.getLabelOrURL(props.value) }}
      </u>
      <template v-else>
        {{ $options.methods.getLabelOrURL(props.value) }}
      </template>
    </div>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'FunctionalFormulaLinkArrayItem',
  mixins: [linkURLField],
}
</script>
