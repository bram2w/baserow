<template>
  <li class="context__menu-item">
    <a
      class="context__menu-item-link"
      :class="{ disabled: !modelAvailable }"
      @click.prevent.stop=";[generateAIFieldValues()]"
    >
      <i class="context__menu-item-icon iconoir-magic-wand"></i>
      {{ $t('gridView.generateCellsValues') }}
    </a>
  </li>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import FieldService from '@baserow_premium/services/field'

export default {
  props: {
    field: {
      type: Object,
      required: true,
    },
    rows: {
      type: Array,
      required: true,
    },
    storePrefix: {
      type: String,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  computed: {
    workspace() {
      return this.$store.getters['workspace/get'](this.database.workspace.id)
    },
    modelAvailable() {
      const aIModels =
        this.workspace.generative_ai_models_enabled[
          this.field.ai_generative_ai_type
        ] || []
      return (
        this.$registry
          .get('field', this.field.type)
          .isEnabled(this.workspace) &&
        aIModels.includes(this.field.ai_generative_ai_model)
      )
    },
  },
  methods: {
    async generateAIFieldValues($event) {
      if (!this.modelAvailable) {
        return
      }

      const rowIds = this.rows.map((row) => row.id)
      const fieldId = this.field.id
      this.$store.dispatch(
        this.storePrefix + 'view/grid/setPendingFieldOperations',
        { fieldId, rowIds, value: true }
      )

      try {
        await FieldService(this.$client).generateAIFieldValues(fieldId, rowIds)
      } catch (error) {
        this.$store.dispatch(
          this.storePrefix + 'view/grid/setPendingFieldOperations',
          { fieldId, rowIds, value: false }
        )
        notifyIf(error, 'field')
      }
      this.$emit('click', $event)
    },
  },
}
</script>
