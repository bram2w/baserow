<template functional>
  <div v-if="props.value" class="array-field__item">
    <div class="array-field__ellipsis" :title="props.value">
      <a
        v-if="props.selected"
        :href="$options.methods.getHref(props.value)"
        target="_blank"
        rel="nofollow noopener noreferrer"
        class="forced-pointer-events-auto"
        @mousedown.stop
        >{{ props.value }}</a
      >
      <u v-else>{{ props.value }}</u>
    </div>
  </div>
</template>

<script>
import linkURLField from '@baserow/modules/database/mixins/linkURLField'
export default {
  name: 'FunctionalFormulaURLArrayItem',
  mixins: [linkURLField],
}
</script>
