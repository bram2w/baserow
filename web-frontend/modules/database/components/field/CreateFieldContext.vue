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
import context from '@/mixins/context'
import FieldForm from '@/modules/database/components/field/FieldForm'
import { notifyIf } from '@/utils/error'

export default {
  name: 'CreateFieldContext',
  components: { FieldForm },
  mixins: [context],
  props: {
    table: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      loading: false
    }
  },
  methods: {
    submit(values) {
      this.loading = true

      const type = values.type
      delete values.type

      this.$store
        .dispatch('field/create', {
          type,
          values,
          table: this.table
        })
        .then(() => {
          this.loading = false
          this.$refs.form.reset()
          this.hide()
        })
        .catch(error => {
          this.loading = false
          notifyIf(error, 'field')
        })
    }
  }
}
</script>
