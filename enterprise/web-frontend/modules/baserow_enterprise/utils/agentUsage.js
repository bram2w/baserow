/**
 * Short token counts: 950, 12.3k, 1.2M.
 */
export function formatTokens(count) {
  const value = Number(count) || 0
  if (value < 1000) {
    return String(value)
  }
  // Decided on the rounded value, so 999,950 reads 1M and not 1000k.
  const thousands = trimDecimal(value / 1000)
  if (Number(thousands) < 1000) {
    return `${thousands}k`
  }
  return `${trimDecimal(value / 1000000)}M`
}

function trimDecimal(value) {
  return (value < 10 ? value.toFixed(1) : Math.round(value).toString()).replace(
    /\.0$/,
    ''
  )
}

/**
 * A cost in USD; amounts below a cent would round to nothing, so they say so.
 */
export function formatCost(cost) {
  const value = Number(cost) || 0
  if (value > 0 && value < 0.01) {
    return '<$0.01'
  }
  return `$${value.toFixed(2)}`
}

/**
 * Whether a cost is known for at least part of the usage. Models without a
 * public price only show their tokens.
 */
export function hasCost(usage) {
  return Number(usage?.cost ?? usage?.total_cost) > 0
}

export function totalTokens(usage) {
  return (
    (Number(usage?.input_tokens ?? usage?.total_input_tokens) || 0) +
    (Number(usage?.output_tokens ?? usage?.total_output_tokens) || 0)
  )
}

export function inputTokens(usage) {
  return Number(usage?.input_tokens ?? usage?.total_input_tokens) || 0
}

export function outputTokens(usage) {
  return Number(usage?.output_tokens ?? usage?.total_output_tokens) || 0
}

export function cachedInputTokens(usage) {
  return (
    Number(usage?.cached_input_tokens ?? usage?.total_cached_input_tokens) || 0
  )
}

/**
 * The browser's timezone, so "today" and "this week" are the viewer's.
 */
export function viewerTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}
