<template>
  <div class="grid-view__head">
    <div
      v-if="includeRowDetails"
      class="grid-view__column"
      :style="{ width: gridViewRowDetailsWidth + 'px' }"
    ></div>
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
      ></CreateFieldContext>
    </div>
  </div>
</template>

<script>
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import GridViewFieldType from '@baserow/modules/database/components/view/grid/GridViewFieldType'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

export default {
  name: 'GridViewHead',
  components: {
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
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
}
</script>
