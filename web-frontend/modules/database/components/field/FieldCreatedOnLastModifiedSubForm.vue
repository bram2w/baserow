<template>
  <div>
    <FieldDateSubForm
      :table="table"
      :default-values="defaultValues"
    ></FieldDateSubForm>
    <div class="control">
      <div class="control__elements">
        <div class="filters__value-timezone">{{ values.timezone }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

import FieldDateSubForm from '@baserow/modules/database/components/field/FieldDateSubForm'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'

export default {
  name: 'FieldCreatedOnLastModifiedSubForm',
  components: { FieldDateSubForm },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: ['timezone'],
      values: {
        timezone: this.getCurrentTimezone(),
      },
    }
  },
  methods: {
    getCurrentTimezone() {
      return new Intl.DateTimeFormat().resolvedOptions().timeZone
    },
  },
}
</script>
