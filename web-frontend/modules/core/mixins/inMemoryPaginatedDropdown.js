import paginatedDropdown from '@baserow/modules/core/mixins/paginatedDropdown'

export default {
  name: 'inMemoryPaginatedDropdown',
  mixins: [paginatedDropdown],
  methods: {
    fetchPage(page = 1, query = '') {
      const start = (page - 1) * this.pageSize
      const results = this.filterItems(query || '')
      return {
        data: {
          count: results.length,
          results: results.slice(start, start + this.pageSize),
        },
      }
    },
    search() {
      this.fetch(this.page, this.query)
    },
  },
}
