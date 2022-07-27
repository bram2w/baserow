<template>
  <Context ref="context">
    <FieldForm
      ref="form"
      :table="table"
      :forced-type="forcedType"
      @submitted="submit"
    >
      <div class="context__form-actions">
        <button
          class="button"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('action.create') }}
        </button>
      </div>
    </FieldForm>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import FieldForm from '@baserow/modules/database/components/field/FieldForm'
import { notifyIf } from '@baserow/modules/core/utils/error'
import { createNewUndoRedoActionGroupId } from '@baserow/modules/database/utils/action'

export default {
  name: 'CreateFieldContext',
  components: { FieldForm },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true,
    },
    forcedType: {
      type: [String, null],
      required: false,
      default: null,
    },
    useActionGroupId: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      loading: false,
    }
  },
  methods: {
    async submit(values) {
      this.loading = true

      const type = values.type
      delete values.type
      const actionGroupId = this.useActionGroupId
        ? createNewUndoRedoActionGroupId()
        : null
      try {
        const {
          forceCreateCallback,
          fetchNeeded,
          newField,
          undoRedoActionGroupId,
        } = await this.$store.dispatch('field/create', {
          type,
          values,
          table: this.table,
          forceCreate: false,
          undoRedoActionGroupId: actionGroupId,
        })
        const callback = async () => {
          await forceCreateCallback()
          this.createdId = null
          this.loading = false
          this.$refs.form.reset()
          this.hide()
          this.$emit('field-created-callback-done', {
            newField,
            undoRedoActionGroupId,
          })
        }
        this.$emit('field-created', { callback, newField, fetchNeeded })
      } catch (error) {
        this.loading = false
        const handledByForm = this.$refs.form.handleErrorByForm(error)
        if (!handledByForm) {
          notifyIf(error, 'field')
        }
      }
    },
  },
}
</script>
