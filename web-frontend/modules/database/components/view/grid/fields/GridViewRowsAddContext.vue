<template>
  <Context>
    <div class="context__menu-title">
      {{ $t('gridViewRowsAddContext.title') }}
    </div>
    <ul class="context__menu">
      <li v-for="rowAmountChoice in rowAmountChoices" :key="rowAmountChoice">
        <a @click="$emit('add-rows', rowAmountChoice)">
          {{ $t('gridViewRowsAddContext.choice', { rowAmountChoice }) }}
        </a>
      </li>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'GridViewRowsAddContext',
  mixins: [context],
  computed: {
    rowAmountChoices() {
      return [5, 10, 20, 50]
    },
  },
}
</script>
