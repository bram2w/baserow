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
import FieldService from '@baserow/modules/database/services/field'
import { notifyIf } from '@baserow/modules/core/utils/error'

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
  },
  computed: {
    modelAvailable() {
      const aIModels =
        this.$store.getters['settings/get'].generative_ai[
          this.field.ai_generative_ai_type
        ] || []
      return (
        this.$registry.get('field', this.field.type).isEnabled() &&
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
