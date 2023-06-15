<template>
  <div>
    <FieldSelectThroughFieldSubForm
      :fields="fields"
      :database="database"
      :default-values="defaultValues"
    ></FieldSelectThroughFieldSubForm>
  </div>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import fieldSubForm from '@baserow/modules/database/mixins/fieldSubForm'
import FieldSelectThroughFieldSubForm from '@baserow/modules/database/components/field/FieldSelectThroughFieldSubForm'

export default {
  name: 'FieldCountSubForm',
  components: { FieldSelectThroughFieldSubForm },
  mixins: [form, fieldSubForm],
  data() {
    return {
      allowedValues: [],
      values: {},
    }
  },
  computed: {
    database() {
      return this.$store.getters['application/get'](this.table.database_id)
    },
    fields() {
      // This part might fail in the future because we can't 100% depend on that the
      // fields in the store are related to the component that renders this. An example
      // is if you edit the field type in a row edit modal of a related table.
      return this.$store.getters['field/getAll']
    },
  },
  validations: {},
}
</script>
