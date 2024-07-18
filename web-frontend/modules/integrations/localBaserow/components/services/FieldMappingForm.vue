<template>
  <div>
    <FormGroup
      v-for="field in fields"
      :key="field.id"
      small-label
      :label="field.name"
      required
    >
      <FieldMapping
        :field-mapping="getFieldMapping(field.id)"
        :placeholder="$t('upsertRowWorkflowActionForm.fieldMappingPlaceholder')"
        @change="updateFieldMapping(field.id, $event)"
      />
    </FormGroup>
  </div>
</template>

<script>
import FieldMapping from '@baserow/modules/integrations/localBaserow/components/services/FieldMapping'

export default {
  name: 'FieldMappingForm',
  components: { FieldMapping },
  props: {
    value: {
      type: Array,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  methods: {
    getFieldMapping(fieldId) {
      return (
        this.value.find(
          (fieldMapping) => fieldMapping.field_id === fieldId
        ) || { enabled: true, field_id: fieldId, value: '' }
      )
    },
    updateFieldMapping(fieldId, changes) {
      const existingMapping = this.value.some(
        ({ field_id: existingId }) => existingId === fieldId
      )
      if (existingMapping) {
        const newMapping = this.value.map((fieldMapping) => {
          if (fieldMapping.field_id === fieldId) {
            return { ...fieldMapping, ...changes }
          }
          return fieldMapping
        })
        this.$emit('input', newMapping)
      } else {
        const newMapping = [...this.value]
        newMapping.push({
          enabled: true,
          field_id: fieldId,
          ...changes,
        })
        this.$emit('input', newMapping)
      }
    },
  },
}
</script>
