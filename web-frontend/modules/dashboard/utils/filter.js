export function shouldResetFilterValues(previous, next) {
  return (
    previous?.mode === 'dropdown' &&
    (next.mode === 'input' ||
      (next.mode === 'dropdown' && previous.multiple && !next.multiple))
  )
}
