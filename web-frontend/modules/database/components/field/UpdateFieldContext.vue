<template>
  <Context ref="context">
    <FieldForm
      ref="form"
      class="context-form"
      :default-values="field"
      @submitted="submit"
    >
      <div class="context-form-actions">
        <button
          class="button"
          :class="{ 'button-loading': loading }"
          :disabled="loading"
        >
          Change
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
    field: {
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
        .dispatch('field/update', {
          field: this.field,
          type,
          values
        })
        .then(() => {
          this.loading = false
          this.$refs.form.reset()
          this.hide()
          this.$emit('update')
        })
        .catch(error => {
          this.loading = false
          notifyIf(error, 'field')
        })
    }
  }
}
</script>
