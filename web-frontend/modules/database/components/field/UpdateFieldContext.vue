<template>
  <Context ref="context">
    <FieldForm
      ref="form"
      :table="table"
      :default-values="field"
      :primary="field.primary"
      @submitted="submit"
    >
      <div class="context__form-actions">
        <button
          class="button"
          :class="{ 'button--loading': loading }"
          :disabled="loading"
        >
          {{ $t('action.change') }}
        </button>
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
  },
  data() {
    return {
      loading: false,
    }
  },
  watch: {
    field() {
      // If the field values are updated via an outside source, think of real time
      // collaboration or via the modal, we want to reset the form so that it contains
      // the correct base values.
      this.$nextTick(() => {
        this.$refs.form.reset()
      })
    },
  },
  methods: {
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
          this.$refs.form.reset()
          this.loading = false
          this.hide()
          this.$emit('updated')
        }
        this.$emit('update', { callback })
      } catch (error) {
        this.loading = false
        notifyIf(error, 'field')
      }
    },
  },
}
</script>
