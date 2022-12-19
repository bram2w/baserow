# Feature flags

Baserow uses basic feature flags currently to allow unfinished features to be merged
and/or released.

## Available Feature Flags

Add/remove features flags to the list below:

## Enabling feature flags

To enable specific feature flags set the environment variable
`FEATURE_FLAGS=feature1,feature2,feature3`. Using `dev.sh` this would look like:

```bash
FEATURE_FLAGS=feature1,feature2,feature3 ./dev.sh xyz
```

You could also use a docker-compose `.env` file and set the FEATURE_FLAGS variable in 
there.

## Enabling all feature flags

Use the `*` feature flag to enable every single feature flag without having to specify 
each one.

```bash
FEATURE_FLAGS=* ./dev.sh xyz
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
# In your feature file:
from django.conf import settings

if "feature1" in settings.FEATURE_FLAGS:
# do the feature
```

### In the Web-frontend

```javascript
methods: {
    someComponentMethod()
    {
        if (this.$featureFlagIsEnabled("feature1")){
            // do the feature
        }
    }
}
```

