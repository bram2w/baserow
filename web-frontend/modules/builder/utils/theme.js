export const themeToColorVariables = (theme) => {
  return [
    { name: 'Primary', value: 'primary', color: theme.primary_color },
    { name: 'Secondary', value: 'secondary', color: theme.secondary_color },
    { name: 'Border', value: 'border', color: theme.border_color },
  ]
}
