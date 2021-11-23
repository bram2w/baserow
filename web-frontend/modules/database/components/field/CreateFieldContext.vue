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

      try {
        const { forceCreateCallback, refreshNeeded } =
          await this.$store.dispatch('field/create', {
            type,
            values,
            table: this.table,
            forceCreate: false,
          })
        const callback = async () => {
          await forceCreateCallback()
          this.createdId = null
          this.loading = false
          this.$refs.form.reset()
          this.hide()
        }
        if (refreshNeeded) {
          this.$emit('refresh', { callback })
        } else {
          await callback()
        }
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
