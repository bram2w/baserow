<template>
  <Context
    ref="context"
    class="field-form-context"
    :overflow-scroll="true"
    :max-height-if-outside-viewport="true"
  >
    <FieldForm
      ref="form"
      :table="table"
      :view="view"
      :default-values="field"
      :primary="field.primary"
      :all-fields-in-table="allFieldsInTable"
      :database="database"
      @submitted="submit"
    >
      <div
        class="context__form-actions context__form-actions--multiple-actions"
      >
        <a @click="cancel">
          {{ $t('action.cancel') }}
        </a>

        <Button :loading="loading" :disabled="loading || fieldTypeDisabled">
          {{ $t('action.save') }}
        </Button>
      </div>
    </FieldForm>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import FieldForm from '@baserow/modules/database/components/field/FieldForm'
import { notifyIf } from '@baserow/modules/core/utils/error'

export default {
  name: 'UpdateFieldContext',
  components: { FieldForm },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    allFieldsInTable: {
      type: Array,
      required: true,
    },
    database: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  computed: {
    // Return the reactive object that can be updated in runtime.
    workspace() {
      return this.$store.getters['workspace/get'](this.database.workspace.id)
    },
    fieldTypeDisabled() {
      return !this.$registry
        .get('field', this.field.type)
        .isEnabled(this.workspace)
    },
  },
  watch: {
    field() {
      // If the field values are updated via an outside source, think of real time
      // collaboration or via the modal, we want to reset the form so that it contains
      // the correct base values.
      this.reset()
    },
  },
  methods: {
    reset() {
      this.$nextTick(() => {
        this.$refs.form && this.$refs.form.reset()
      })
    },
    async submit(values) {
      this.loading = true

      const type = values.type
      delete values.type

      try {
        const forceUpdateCallback = await this.$store.dispatch('field/update', {
          field: this.field,
          type,
          values,
          forceUpdate: false,
        })
        // The callback must be called as soon the parent page has refreshed the rows.
        // This is to prevent incompatible values when the field changes before the
        // actual column row has been updated. If there is nothing to refresh then the
        // callback must still be called.
        const callback = async () => {
          await forceUpdateCallback()
          this.$refs.form && this.$refs.form.reset()
          this.loading = false
          this.hide()
          this.$emit('updated')
        }
        this.$emit('update', { callback })
      } catch (error) {
        this.loading = false
        let handledByForm = false
        if (this.$refs.form) {
          handledByForm = this.$refs.form.handleErrorByForm(error)
        }
        if (!handledByForm) {
          notifyIf(error, 'field')
        }
      }
    },
    cancel() {
      this.reset()
      this.hide()
    },
  },
}
</script>
