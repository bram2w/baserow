<template>
  <Modal>
    <h2 class="box-title">Create new table</h2>
    <Error :error="error"></Error>
    <TableForm ref="tableForm" @submitted="submitted">
      <div class="actions">
        <div class="align-right">
          <button
            class="button button-large"
            :class="{ 'button-loading': loading }"
            :disabled="loading"
          >
            Add table
          </button>
        </div>
      </div>
    </TableForm>
  </Modal>
</template>

<script>
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'

import TableForm from './TableForm'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal, error],
  props: {
    application: {
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
    async submitted(values) {
      this.loading = true
      this.hideError()

      try {
        const table = await this.$store.dispatch('table/create', {
          database: this.application,
          values,
        })
        this.loading = false
        this.hide()

        // Redirect to the newly created table.
        this.$nuxt.$router.push({
          name: 'database-table',
          params: {
            databaseId: this.application.id,
            tableId: table.id,
          },
        })
      } catch (error) {
        this.loading = false
        this.handleError(error, 'application')
      }
    },
  },
}
</script>
