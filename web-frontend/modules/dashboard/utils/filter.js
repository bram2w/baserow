export function shouldResetFilterValues(previous, next) {
  return (
    previous != null &&
    (previous.mode !== next.mode ||
      (next.mode === 'dropdown' && previous.multiple !== next.multiple))
  )
}
