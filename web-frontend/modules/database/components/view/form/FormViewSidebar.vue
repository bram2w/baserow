<template>
  <div class="form-view__sidebar">
    <div class="form-view__sidebar-fields">
      <div class="form-view__sidebar-fields-head">
        <div class="form-view__sidebar-fields-title">Fields</div>
        <ul v-if="!readOnly" class="form-view__sidebar-fields-actions">
          <li v-show="fields.length > 0">
            <a
              @click="
                updateFieldOptionsOfFields(
                  view,
                  fields,
                  { enabled: true },
                  true
                )
              "
              >add all</a
            >
          </li>
          <li v-show="enabledFields.length > 0">
            <a
              @click="
                updateFieldOptionsOfFields(
                  view,
                  enabledFields,
                  { enabled: false },
                  true
                )
              "
              >remove all</a
            >
          </li>
        </ul>
      </div>
      <div v-if="fields.length > 0" class="form-view__sidebar-fields-list">
        <FormViewSidebarField
          v-for="field in fields"
          :key="field.id"
          v-sortable="{
            enabled: !readOnly,
            id: field.id,
            update: order,
          }"
          :field="field"
          :read-only="readOnly"
          @updated-field-options="
            updateFieldOptionsOfField(view, field, $event)
          "
        >
        </FormViewSidebarField>
      </div>
      <p v-else class="form-view__sidebar-fields-description">
        All the fields are in the form.
      </p>
      <div v-if="!readOnly">
        <a
          ref="createFieldContextLink"
          @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
        >
          <i class="fas fa-plus"></i>
          Create new field
        </a>
        <CreateFieldContext
          ref="createFieldContext"
          :table="table"
          @refresh="$emit('refresh', $event)"
        ></CreateFieldContext>
      </div>
    </div>
  </div>
</template>

<script>
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import formViewHelpers from '@baserow/modules/database/mixins/formViewHelpers'
import FormViewSidebarField from '@baserow/modules/database/components/view/form/FormViewSidebarField'

export default {
  name: 'FormViewSidebar',
  components: { CreateFieldContext, FormViewSidebarField },
  mixins: [formViewHelpers],
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
    enabledFields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  methods: {
    order(order) {
      this.$emit('ordered-fields', order)
    },
  },
}
</script>
