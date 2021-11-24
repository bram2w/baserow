<template>
  <RowEditFieldSingleSelect :read-only="true" :field="field">
  </RowEditFieldSingleSelect>
</template>

<script>
import RowEditFieldSingleSelect from '@baserow/modules/database/components/row/RowEditFieldSingleSelect'
export default {
  name: 'RowEditFieldSingleSelectReadOnly',
  components: { RowEditFieldSingleSelect },
}
</script>
