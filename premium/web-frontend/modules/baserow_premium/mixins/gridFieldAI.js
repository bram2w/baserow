import { notifyIf } from '@baserow/modules/core/utils/error'

import FieldService from '@baserow_premium/services/field'

export default {
  computed: {
    // Indicates if the cell is currently being generated together with other cells in
    // bulk via the apposite grid-view menu.
    generating() {
      return this.isGenerating(this.$parent, this.$props)
    },
    modelAvailable() {
      return this.isModelAvailable(this.$parent, this.$props)
    },
  },
  methods: {
    isGenerating(parent, props) {
      return parent.row._.pendingFieldOps?.find(
        (fieldName) => fieldName === `field_${props.field.id}`
      )
    },
    isModelAvailable(parent, props) {
      const aIModels =
        parent.$store.getters['settings/get'].generative_ai[
          props.field.ai_generative_ai_type
        ] || []
      return (
        parent.$registry.get('field', props.field.type).isEnabled() &&
        aIModels.includes(props.field.ai_generative_ai_model)
      )
    },
    async generate() {
      const rowId = this.$parent.row.id
      this.$store.dispatch(
        this.storePrefix + 'view/grid/setPendingFieldOperations',
        { fieldId: this.field.id, rowIds: [rowId], value: true }
      )
      try {
        await FieldService(this.$client).generateAIFieldValues(this.field.id, [
          rowId,
        ])
      } catch (error) {
        notifyIf(error, 'field')
        this.$store.dispatch(
          this.storePrefix + 'view/grid/setPendingFieldOperations',
          { fieldId: this.field.id, rowIds: [rowId], value: false }
        )
      }
    },
  },
}
