export const SearchModes = {
  // Use this mode to search rows using LIKE operators against each
  // field type, and return an accurate `count` in the response.
  // This method is slow after a few thousand rows and dozens of fields.
  MODE_COMPAT: 'compat',
  // Use this mode to search rows using Postgres full-text search against
  // each field type, and provide a `count` in the response. This
  // method is much faster as tables grow in size.
  MODE_FT_WITH_COUNT: 'full-text-with-count',
}

export function getDefaultSearchModeFromEnv($config) {
  return $config.BASEROW_USE_PG_FULLTEXT_SEARCH === 'true'
    ? SearchModes.MODE_FT_WITH_COUNT
    : SearchModes.MODE_COMPAT
}
