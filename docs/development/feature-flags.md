# Feature flags

Baserow uses basic feature flags currently to allow unfinished features to be merged
and/or released.

## Available Feature Flags

Add/remove features flags to the list below:

- `ai-providers` — AI provider management for the instance admin area and for
  workspace settings.
- `button-field`: enables the button field type
  ([#1722](https://github.com/baserow/baserow/issues/1722)).

### Preparing the `ai-providers` feature

The schema migration preserves AI Agent provider/model selections and legacy
credentials. Existing provider models gain AI Agent eligibility without losing
their other feature choices. If the flag remains disabled, upgrading does not
require importing providers or republishing applications.

For installations already using this experimental feature, pause provider/model
changes before migrating and until all previous backend/worker processes have
stopped. Reload administrator/editor browsers before resuming changes. An upgrade
with the services stopped can retain the flag; do not switch to legacy resolution
unless the legacy configuration still supports the selected providers and models.

AI Agent integration overrides use their own complete connection settings. When a
built-in provider override omits `models`, it inherits the allowed model list;
an explicit empty list allows no models. Incomplete overrides can only restrict
inherited models, and their connection fields are ignored. Complete overrides no
longer inherit omitted optional settings such as OpenAI's `base_url` or
`organization`; supply those explicitly if required. These rules also apply with
the feature disabled, including to existing published integrations.

The following steps apply when enabling database-backed providers on an existing
installation.

There are two sources of legacy configuration and both must be imported: AI provider
**environment variables** become instance-level providers, and each workspace's legacy
`generative_ai_models_settings` JSON becomes workspace-owned providers. Run the whole
sequence with the flag still disabled, because until a workspace's legacy JSON is
imported the new UI reports no workspace provider while that JSON is still what
resolves at runtime.

1. Before deploying the release, keep `ai-providers` disabled. If the installation
   uses `FEATURE_FLAGS=*`, first make a separate configuration-only rollout of the
   currently installed release with an explicit list of the other required flags;
   there is no negative override for one flag. Wait for every wildcard-configured
   web and worker process to drain before deploying the new image. Do not combine
   this configuration change with a rolling image update: old processes would still
   enable `ai-providers`. If the platform cannot roll out configuration separately,
   stop the old processes before starting the new release with the explicit list.
2. Deploy the release and let the old web and worker processes drain. Pause changes
   to instance and workspace AI provider settings until the import is complete and
   the flag has been enabled; otherwise a workspace can change its legacy JSON after
   the command has read it.
   The new Google and Groq provider types have no environment variables and are
   configured in the admin UI only. Older frontend bundles do not have those
   provider types in their registry and cannot safely render a workspace payload
   containing them, so add either provider only after every old frontend process
   has drained. Draining frontend processes does not replace JavaScript already
   loaded in a browser tab: before adding either provider, require active users to
   reload Baserow (or close and reopen it) onto the new frontend assets. Keep the
   settings-write pause in place until that client cutover is complete.
   Administrator/editor tabs must also reload before provider/model changes resume,
   because older editors do not include AI Agent eligibility in new model settings.
3. Preview both scopes. The command writes nothing without `--apply`:

```bash
just b manage migrate_ai_provider_settings --scope instance
just b manage migrate_ai_provider_settings --scope workspace
```

4. Review every warning. Repair or explicitly accept each incomplete legacy setting
   and each difference from an existing database provider before proceeding. The
   importer preserves the database provider in a conflict, and an incomplete
   workspace override can inherit the instance provider after the flag is enabled.
   Then apply each scope atomically, instance first:

```bash
just b manage migrate_ai_provider_settings --scope instance --apply
just b manage migrate_ai_provider_settings --scope workspace --apply
```

The release migration marks every existing database-backed model as available to AI
Agent services used by Automation nodes and Application Builder actions while
preserving its existing eligibility. The import command uses a fixed compatibility
default of AI Fields and AI Agent for models imported from legacy environment or
workspace settings. Those consumers used the unfiltered model list before per-feature
eligibility existed; administrators can narrow either eligibility after the cutover.

5. Redeploy or restart every web, backend, and worker process with `ai-providers`
   enabled, then wait for every feature-disabled process to drain before ending
   the settings-write pause. This prevents one generation from resolving legacy
   settings while another resolves the imported database settings. Wildcard
   installations can now restore `FEATURE_FLAGS=*`.
6. Republish any Application Builder site or Automation workflow that uses an AI
   integration without its own provider override. Publications created before the
   switch contain a snapshot of the inherited legacy workspace settings; republishing
   replaces that snapshot with live database-backed workspace inheritance. Explicit
   per-integration provider overrides remain self-contained and do not need this step.
   Republishing also publishes pending draft changes. Review those changes first;
   a publication left on its old complete override does not adopt database credential
   rotation or model-eligibility changes.

The command never prints credentials and preserves provider types already configured
at the selected scope, so both imports are safe to run again — only missing
provider types are imported.
Rerunning an import does not synchronize later legacy edits into existing database
providers. Review and reconcile those differences before enabling the feature.

Disabling the feature uses legacy configuration; database provider changes are not
copied back to it. Keep usable legacy settings for rollback, and verify them before
switching. Retain the provider schema during a flag rollback.

The command does not import Kuma's legacy model or provider-native credentials.
Kuma continues to use that legacy configuration when its database selection is
unconfigured or invalid. An explicit instance or workspace disable remains
authoritative and does not fall back. An administrator can clear an instance
database selection with **Use legacy environment model**, which displays the
configured model.

## Enabling feature flags

To enable specific feature flags set the environment variable
`FEATURE_FLAGS=feature1,feature2,feature3`. Using `just` this would look like:

```bash
FEATURE_FLAGS=feature1,feature2,feature3 just dc-dev up -d
```

You could also add the variable to your `.env.docker-dev` file (for Docker development)
or `.env.local` file (for local development).

## Enabling all feature flags

Use the `*` feature flag to enable every single feature flag without having to specify
each one.

```bash
FEATURE_FLAGS=* just dc-dev up -d
```

## Naming convention

Feature flags should be:

1. Alphanumeric with dashes.
2. Not start or end with spaces (flags from the env variable will be trimmed for ease of
   use).
3. Unique per feature.

## Creating a feature flag

### In the Backend

```python
# Add variable with feature flag to baserow.core.feature_flag in format
# FF_<FEATURE_NAME> = "feature_name"
# i.e.
FF_FEATURE1 = "feature1"

# In your feature file import flag you need and feature flag function
from baserow.core.feature_flag import FF_FEATURE1, feature_flag_is_enabled

# Use to check if feature is enabled
if feature_flag_is_enabled(FF_FEATURE1):
    # do the feature

# or if you want to raise exception if the feature is not enabled
feature_flag_is_enabled(FF_FEATURE1, raise_if_disabled=True)
```

### In the Web-frontend

```javascript
// add feature flag variable in @core/plugins/featureFlags.js in format
// FF_<FEATURE_NAME> = "feature_name"
// i.e.
export const FF_FEATURE1 = "feature1";

methods: {
    someComponentMethod();
    {
        if (this.$featureFlagIsEnabled(FF_FEATURE1)) {
            // do the feature
        }
    }
}
```
