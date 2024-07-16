<template>
  <div>
    <InjectedFormulaInputGroup
      v-model="fieldValue"
      :disabled="!fieldMapping.enabled"
      v-bind="$attrs"
      class="margin-bottom-2"
    >
      <template #after-input>
        <div ref="editFieldMappingOpener">
          <Button
            type="secondary"
            size="regular"
            icon="iconoir-more-vert"
            @click="openContext"
          ></Button>
        </div>
        <FieldMappingContext
          ref="fieldMappingContext"
          :field-mapping="fieldMapping"
          @edit="$emit('change', $event)"
        ></FieldMappingContext>
      </template>
    </InjectedFormulaInputGroup>
  </div>
</template>

<script>
import InjectedFormulaInputGroup from '@baserow/modules/core/components/formula/InjectedFormulaInputGroup'
import FieldMappingContext from '@baserow/modules/integrations/localBaserow/components/services/FieldMappingContext'

export default {
  name: 'FieldMapping',
  components: { FieldMappingContext, InjectedFormulaInputGroup },
  props: {
    fieldMapping: {
      type: Object,
      required: true,
    },
  },
  computed: {
    fieldValue: {
      get() {
        return this.fieldMapping.value
      },
      set(value) {
        this.$emit('change', { value })
      },
    },
  },
  methods: {
    openContext() {
      this.$refs.fieldMappingContext.toggle(
        this.$refs.editFieldMappingOpener,
        'bottom',
        'left',
        4
      )
    },
  },
}
</script>
