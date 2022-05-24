<template>
  <div class="grid-view__head">
    <div
      v-if="includeRowDetails"
      class="grid-view__column"
      :style="{ width: gridViewRowDetailsWidth + 'px' }"
    >
      <GridViewRowIdentifierDropdown
        v-if="!readOnly"
        :row-indetifier-type-selected="view.row_identifier_type"
        @change="onChangeIdentifierDropdown"
      ></GridViewRowIdentifierDropdown>
    </div>
    <GridViewFieldType
      v-for="field in fields"
      :key="'field-type-' + field.id"
      :table="table"
      :view="view"
      :field="field"
      :filters="view.filters"
      :include-field-width-handles="includeFieldWidthHandles"
      :read-only="readOnly"
      :store-prefix="storePrefix"
      @refresh="$emit('refresh', $event)"
      @dragging="$emit('dragging', $event)"
      @field-created="$emit('field-created', $event)"
      @update-inserted-field-order="updateInsertedFieldOrder"
    ></GridViewFieldType>
    <div
      v-if="includeAddField && !readOnly"
      class="grid-view__column"
      :style="{ width: 100 + 'px' }"
    >
      <a
        ref="createFieldContextLink"
        class="grid-view__add-column"
        @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
      >
        <i class="fas fa-plus"></i>
      </a>
      <CreateFieldContext
        ref="createFieldContext"
        :table="table"
        @field-created="$emit('field-created', $event)"
      ></CreateFieldContext>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import GridViewFieldType from '@baserow/modules/database/components/view/grid/GridViewFieldType'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'
import GridViewRowIdentifierDropdown from '@baserow/modules/database/components/view/grid/GridViewRowIdentifierDropdown'

export default {
  name: 'GridViewHead',
  components: {
    GridViewRowIdentifierDropdown,
    GridViewFieldType,
    CreateFieldContext,
  },
  mixins: [gridViewHelpers],
  props: {
    fields: {
      type: Array,
      required: true,
    },
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    includeFieldWidthHandles: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    includeRowDetails: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    includeAddField: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    includeGridViewIdentifierDropdown: {
      type: Boolean,
      required: false,
      default: () => false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    /**
     * After newField is created pressing "insert left" or "insert right" button,
     * we need to move the newField into the correct order position.
     * This function find the correct order position and update the fieldOptions accordingly.
     **/
    async updateInsertedFieldOrder({ position, newField, fromField }) {
      const newOrder = this.fields.map((field) => field.id)
      const oldIndex = newOrder.indexOf(newField.id)
      const offset = position === 'left' ? 0 : 1
      const newIndex = newOrder.indexOf(fromField.id) + offset
      newOrder.splice(newIndex, 0, newOrder.splice(oldIndex, 1)[0])

      try {
        await this.$store.dispatch(
          `${this.storePrefix}view/grid/updateFieldOptionsOrder`,
          {
            order: newOrder,
          }
        )
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    async onChangeIdentifierDropdown(rowIdentifierType) {
      try {
        await this.$store.dispatch('view/update', {
          view: this.view,
          values: { row_identifier_type: rowIdentifierType },
        })
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
