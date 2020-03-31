<template>
  <Context ref="context">
    <FieldForm ref="form" class="context-form" @submitted="submit">
      <div class="context-form-actions">
        <button
          class="button"
          :class="{ 'button-loading': loading }"
          :disabled="loading"
        >
          Create
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
        await this.$store.dispatch('field/create', {
          type,
          values,
          table: this.table,
        })
        this.loading = false
        this.$refs.form.reset()
        this.hide()
      } catch (error) {
        this.loading = false
        notifyIf(error, 'field')
      }
    },
  },
}
</script>
