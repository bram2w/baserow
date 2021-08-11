<template>
  <Context ref="context">
    <FieldForm ref="form" :table="table" @submitted="submit">
      <div class="context__form-actions">
        <button
          class="button"
          :class="{ 'button--loading': loading }"
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
      const fieldType = this.$registry.get('field', type)
      delete values.type

      try {
        const forceCreateCallback = await this.$store.dispatch('field/create', {
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
        if (fieldType.shouldRefreshWhenAdded()) {
          this.$emit('refresh', { callback })
        } else {
          await callback()
        }
      } catch (error) {
        this.loading = false
        notifyIf(error, 'field')
      }
    },
  },
}
</script>
