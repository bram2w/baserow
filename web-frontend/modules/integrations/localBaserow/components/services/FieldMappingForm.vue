<template>
  <div>
    <FieldMapping
      v-for="field in fields"
      :key="field.id"
      :field="field"
      :value="getFieldMappingValue(field.id)"
      @change="updateFieldMapping($event, field.id)"
    ></FieldMapping>
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
    getFieldMappingValue(fieldId) {
      const mapping = this.value.find(
        (fieldMapping) => fieldMapping.field_id === fieldId
      )
      return mapping?.value || ''
    },
    updateFieldMapping(newValue, fieldId) {
      const event = { field_id: fieldId, value: newValue }
      const existingMapping = this.value.some(
        ({ field_id: existingId }) => existingId === fieldId
      )
      if (existingMapping) {
        const newMapping = this.value.map((fieldMapping) => {
          if (fieldMapping.field_id === fieldId) {
            return { ...fieldMapping, ...event }
          }
          return fieldMapping
        })
        this.$emit('input', newMapping)
      } else {
        // It already exists
        const newMapping = [...this.value]
        newMapping.push({
          field_id: fieldId,
          ...event,
        })
        this.$emit('input', newMapping)
      }
    },
  },
}
</script>
