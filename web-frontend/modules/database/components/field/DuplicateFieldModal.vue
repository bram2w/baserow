<template>
  <Modal :tiny="true" @show="hideError()">
    <h2 class="box__title">
      {{ $t('duplicateFieldContext.duplicate') }}
    </h2>
    <Error :error="error"></Error>
    <form @submit.prevent="duplicateField()">
      <div class="control margin-bottom-1">
        <div class="control__elements">
          <Checkbox v-model="duplicateData" :disabled="true">
            {{ $t('duplicateFieldContext.cloneData') }} ({{
              $t('duplicateFieldContext.soon')
            }})
          </Checkbox>
        </div>
      </div>
      <div class="actions actions--right">
        <button
          class="button button--large button--overflow"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('action.duplicate') }}
        </button>
      </div>
    </form>
  </Modal>
</template>

<script>
import { mapGetters } from 'vuex'
import error from '@baserow/modules/core/mixins/error'
import modal from '@baserow/modules/core/mixins/modal'
import { clone } from '@baserow/modules/core/utils/object'
import { createNewUndoRedoActionGroupId } from '@baserow/modules/database/utils/action'

export default {
  name: 'DuplicateFieldModal',
  mixins: [modal, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
    fromField: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      loading: false,
      duplicateData: false,
    }
  },
  computed: {
    existingFieldName() {
      return this.fields.map((field) => field.name)
    },
    ...mapGetters({
      fields: 'field/getAll',
    }),
  },
  methods: {
    async duplicateField() {
      this.hideError()
      this.loading = true

      const values = clone(this.fromField)
      const type = values.type
      delete values.type
      delete values.id
      values.primary = false

      const baseName = values.name

      // Prevents name collision
      let index = 2
      while (this.existingFieldName.includes(`${baseName} ${index}`)) {
        index += 1
      }
      values.name = `${baseName} ${index}`

      const actionGroupId = createNewUndoRedoActionGroupId()

      try {
        const { forceCreateCallback, fetchNeeded, newField } =
          await this.$store.dispatch('field/create', {
            type,
            values,
            table: this.table,
            forceCreate: false,
            undoRedoActionGroupId: actionGroupId,
          })
        const callback = async () => {
          await forceCreateCallback()
          this.loading = false
          this.hide()
          // GridViewHead will update the order of the fields
          this.$emit('move-field', {
            newField,
            position: 'right',
            fromField: this.fromField,
            undoRedoActionGroupId: actionGroupId,
          })
        }
        this.$emit('field-created', { callback, newField, fetchNeeded })
      } catch (error) {
        this.loading = false
        this.handleError(error)
      }
    },
  },
}
</script>
