// Per tab, because the whole tab is redirected to the provider and back.
const STORAGE_KEY = 'baserow.oauth2IntegrationFlow'

/**
 * Remembers that this tab started connecting an integration, so the outcome
 * is only shown for a flow the user actually started and a crafted link
 * carrying an outcome shows nothing.
 */
export function startOAuth2Flow(integrationId, returnUrl) {
  try {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ integrationId, returnUrl })
    )
  } catch {}
}

export function getOAuth2Flow() {
  try {
    return JSON.parse(window.sessionStorage.getItem(STORAGE_KEY)) || null
  } catch {
    return null
  }
}

export function clearOAuth2Flow() {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY)
  } catch {}
}
