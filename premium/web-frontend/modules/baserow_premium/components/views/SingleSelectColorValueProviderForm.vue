<template>
  <div>
    <div class="margin-bottom-2">
      {{ $t('singleSelectColorValueProviderForm.chooseAColor') }}
    </div>
    <ChooseSingleSelectField
      :view="view"
      :table="table"
      :fields="selectFields"
      :value="value"
      @input="$emit('update', { field: $event })"
    />
  </div>
</template>

<script>
import ChooseSingleSelectField from '@baserow/modules/database/components/field/ChooseSingleSelectField.vue'

export default {
  name: 'SingleSelectColorValueProviderForm',
  components: { ChooseSingleSelectField },
  props: {
    options: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    selectFields() {
      return this.fields.filter(({ type }) => type === 'single_select')
    },
    value() {
      return this.options && this.options.field
    },
  },
}
</script>
