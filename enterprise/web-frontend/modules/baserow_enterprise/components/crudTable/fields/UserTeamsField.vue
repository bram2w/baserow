<template>
  <ExpandOnOverflowList ref="expandOnOverflow" :row="row" :column="column">
    <template #no-records>
      {{ $t('userTeamsField.no_records') }}
    </template>
  </ExpandOnOverflowList>
</template>
<script>
import ExpandOnOverflowList from '@baserow/modules/core/components/crudTable/ExpandOnOverflowList'

/**
 * Displays a list of a teams with a modal displaying any teams that do not fit.
 */
export default {
  name: 'UserTeamsField',
  components: {
    ExpandOnOverflowList,
  },
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
}
</script>
