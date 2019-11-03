<template>
  <Modal>
    <h2 class="box-title">Create new table</h2>
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
import TableForm from './TableForm'

import modal from '@/mixins/modal'

export default {
  name: 'CreateTableModal',
  components: { TableForm },
  mixins: [modal],
  props: {
    application: {
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
    submitted(values) {
      this.loading = true
      this.$store
        .dispatch('table/create', { database: this.application, values })
        .then(() => {
          this.loading = false
          this.hide()
        })
        .catch(() => {
          this.loading = false
        })
    }
  }
}
</script>
