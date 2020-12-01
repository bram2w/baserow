<template>
  <Modal>
    <h2 class="box__title">Delete {{ table.name }}</h2>
    <Error :error="error"></Error>
    <div>
      <p>
        Are you sure you want to delete the table
        <strong>{{ table.name }}</strong
        >? All the related views and data will be permanently deleted.
      </p>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large button--error"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
            @click="deleteTable()"
          >
            Delete table
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
  name: 'DeleteTableModal',
  mixins: [modal, error],
  props: {
    database: {
      type: Object,
      required: true,
    },
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
    async deleteTable() {
      this.hideError()
      this.loading = true
      const { database, table } = this

      try {
        await this.$store.dispatch('table/delete', { database, table })
        this.hide()
      } catch (error) {
        this.handleError(error, 'table')
      }

      this.loading = false
    },
  },
}
</script>
