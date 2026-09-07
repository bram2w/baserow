// These providers share the backend AI_PROVIDER_TYPES settings contract.
// Extension providers keep their authoritative integration model lists.
const builtInProviderTypes = new Set([
  'openai',
  'anthropic',
  'google',
  'groq',
  'mistral',
  'ollama',
  'openrouter',
])

/**
 * Resolve the AI Agent models shown by the client using the same precedence as
 * the backend.
 *
 * A complete integration override owns its connection. Built-in providers
 * inherit the model allowlist when their override omits models; an explicit
 * list, including an empty one, remains authoritative. A partial override can
 * only narrow the feature-filtered workspace list.
 */
export function getEffectiveAIAgentModels({
  workspaceModels = [],
  integrationSettings = null,
  modelType = null,
}) {
  if (!integrationSettings || typeof integrationSettings !== 'object') {
    return workspaceModels
  }

  const integrationModels = Array.isArray(integrationSettings.models)
    ? integrationSettings.models
    : []
  const hasModels = Object.prototype.hasOwnProperty.call(
    integrationSettings,
    'models'
  )

  if (modelType?.isIntegrationSettingsComplete(integrationSettings)) {
    if (!hasModels && builtInProviderTypes.has(modelType.getType())) {
      return workspaceModels
    }
    return integrationModels
  }

  if (!hasModels) {
    return workspaceModels
  }

  const enabledModels = new Set(workspaceModels)
  return integrationModels.filter((model) => enabledModels.has(model))
}
