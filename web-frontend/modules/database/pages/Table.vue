<template>
  <div>
    <header class="layout-col-3-1 header">
      <ul class="header-filter">
        <li class="header-filter-item">&nbsp;</li>
      </ul>
      <ul class="header-info">
        <li>{{ database }}</li>
        <li>{{ table }}</li>
      </ul>
    </header>
  </div>
</template>

<script>
export default {
  layout: 'app',
  props: {
    id: {
      type: Number,
      required: true
    },
    tableId: {
      type: Number,
      required: true
    }
  },
  asyncData({ store, params, redirect }) {
    // @TODO figure out why the id's aren't converted to an int in the route.
    const databaseId = parseInt(params.id)
    const tableId = parseInt(params.tableId)

    return store
      .dispatch('table/preSelect', { databaseId, tableId })
      .then(data => {
        return { database: data.database, table: data.table }
      })
      .catch(() => {
        // If something went wrong this will probably mean that the user doesn't have
        // access to the database so we will need to redirect back to the index page.
        redirect({ name: 'app' })
      })
  }
}
</script>
