export default (client, baseUrl) => {
  return {
    /**
     * @param {number} page The page number to fetch.
     * @param {{searchQuery}} searchQuery A search term to filter results.
     * @param {[{direction:string, key:string}]} sorts An ordered list of sorts to
     * apply to the results.
     */
    fetchPage(page, searchQuery, sorts) {
      const params = { page }
      if (searchQuery) {
        params.search = searchQuery
      }
      if (sorts.length > 0) {
        params.sorts = sorts
          .map((s) => {
            const direction = s.direction === 'asc' ? '-' : '+'
            return `${direction}${s.key}`
          })
          .join(',')
      }
      return client.get(baseUrl, { params })
    },
  }
}
