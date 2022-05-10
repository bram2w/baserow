<template>
  <div>
    <Radio
      v-for="field in singleSelectFields"
      :key="field.id"
      :value="field.id"
      :model-value="value"
      :loading="loading && field.id === value"
      :disabled="loading || readOnly"
      @input="$emit('input', $event)"
      >{{ field.name }}</Radio
    >
    <div v-if="!readOnly" class="margin-top-2">
      <a
        ref="createFieldContextLink"
        class="choose-select-field__link margin-right-auto"
        @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
      >
        <i class="fas fa-plus"></i>
        {{ $t('chooseSingleSelectField.addSelectField') }}
      </a>
      <CreateFieldContext
        ref="createFieldContext"
        :table="table"
        :forced-type="singleSelectFieldType"
        @field-created="$event.callback()"
      ></CreateFieldContext>
    </div>
  </div>
</template>

<script>
import { SingleSelectFieldType } from '@baserow/modules/database/fieldTypes'
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'

export default {
  name: 'ChooseSingleSelectField',
  components: { CreateFieldContext },
  props: {
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: false,
      default: false,
    },
    value: {
      required: true,
      validator() {
        return true
      },
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  computed: {
    singleSelectFieldType() {
      return SingleSelectFieldType.getType()
    },
    singleSelectFields() {
      return this.fields.filter(
        (field) => field.type === this.singleSelectFieldType
      )
    },
  },
}
</script>
