<template>
  <form @submit.prevent>
    <FormInput
      v-model="values.table_id"
      type="number"
      small-label
      :label="$t('localBaserowListRowsForm.tableFieldLabel')"
      :placeholder="$t('localBaserowListRowsForm.tableFieldPlaceHolder')"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['table_id'],
      values: {
        table_id: null,
      },
    }
  },
}
</script>
