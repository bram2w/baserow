<template>
  <form @submit.prevent>
    <FormInput
      v-model="values.view_id"
      type="number"
      small-label
      :label="$t('localBaserowListRowsForm.viewFieldLabel')"
      :placeholder="$t('localBaserowListRowsForm.viewFieldPlaceHolder')"
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
      allowedValues: ['view_id'],
      values: {
        view_id: null,
      },
    }
  },
}
</script>
