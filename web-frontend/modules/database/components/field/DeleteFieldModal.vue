<template>
  <Modal>
    <h2 class="box__title">Delete {{ field.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to delete the field
        <strong>{{ field.name }}</strong
        >? All the data, filters and sortings related to the field will be
        permanently deleted.
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteField()"
          >
            Delete field
          </button>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

export default {
  name: 'DeleteFieldModal',
  mixins: [modal, error],
  props: {
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
  methods: {
    async deleteField() {
      this.hideError()
      this.loading = true
      const { field } = this

      try {
        await this.$store.dispatch('field/deleteCall', field)
        this.$emit('delete')
        this.$store.dispatch('field/forceDelete', field)
        this.hide()
      } catch (error) {
        if (error.response && error.response.status === 404) {
          this.$emit('delete')
          this.$store.dispatch('field/forceDelete', field)
          this.hide()
        } else {
          this.handleError(error, 'field')
        }
      }

      this.loading = false
    },
  },
}
</script>
