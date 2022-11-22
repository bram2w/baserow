<template>
  <div class="form-view__sidebar">
    <div class="form-view__sidebar-fields">
      <div class="form-view__sidebar-fields-head">
        <div class="form-view__sidebar-fields-title">Fields</div>
        <ul
          v-if="!readOnly && !isDeactivated"
          class="form-view__sidebar-fields-actions"
        >
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
              >{{ $t('formSidebar.actions.addAll') }}</a
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
              >{{ $t('formSidebar.actions.removeAll') }}</a
            >
          </li>
        </ul>
      </div>
      <div v-if="fields.length > 0" class="form-view__sidebar-fields-list">
        <FormViewSidebarField
          v-for="field in fields"
          :key="field.id"
          v-sortable="{
            enabled: !readOnly && !isDeactivated,
            id: field.id,
            update: order,
          }"
          :field="field"
          :read-only="readOnly || isDeactivated"
          @updated-field-options="
            updateFieldOptionsOfField(view, field, $event)
          "
        >
        </FormViewSidebarField>
      </div>
      <p v-else class="form-view__sidebar-fields-description">
        {{ $t('formSidebar.fieldsDescription') }}
      </p>
      <div v-if="!readOnly && !isDeactivated">
        <a
          ref="createFieldContextLink"
          @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
        >
          <i class="fas fa-plus"></i>
          {{ $t('formSidebar.actions.addField') }}
        </a>
        <CreateFieldContext
          ref="createFieldContext"
          :table="table"
          @field-created="$event.callback()"
        ></CreateFieldContext>
      </div>
    </div>
    <div class="form-view__sidebar-prefill-or-hide-link">
      <a @click="showFormPrefillOrHideModal">
        <i class="fas fa-question-circle"></i>
        {{ $t('formSidebar.prefillOrHideInfoLink') }}
      </a>
      <FormPrefillOrHideModal
        ref="formPrefillOrHideModal"
      ></FormPrefillOrHideModal>
    </div>
  </div>
</template>

<script>
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'
import formViewHelpers from '@baserow/modules/database/mixins/formViewHelpers'
import FormViewSidebarField from '@baserow/modules/database/components/view/form/FormViewSidebarField'
import FormPrefillOrHideModal from '@baserow/modules/database/components/view/form/FormPrefillOrHideModal'

export default {
  name: 'FormViewSidebar',
  components: {
    FormPrefillOrHideModal,
    CreateFieldContext,
    FormViewSidebarField,
  },
  mixins: [formViewHelpers],
  props: {
    database: {
      type: Object,
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
  computed: {
    modeType() {
      return this.$registry.get('formViewMode', this.view.mode)
    },
    isDeactivated() {
      return (
        !this.readOnly && this.modeType.isDeactivated(this.database.group.id)
      )
    },
  },
  methods: {
    order(order) {
      this.$emit('ordered-fields', order)
    },
    showFormPrefillOrHideModal() {
      this.$refs.formPrefillOrHideModal.show()
    },
  },
}
</script>
