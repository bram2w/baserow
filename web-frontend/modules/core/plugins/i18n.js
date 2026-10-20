import { setMomentLocale } from '@baserow/modules/core/moment'

export default defineNuxtPlugin({
  name: 'i18n',
  async setup(nuxtApp) {
    const { $i18n } = nuxtApp
    // Resolved lazily, because the first call creates the indicator with its
    // options, and those must come from the `NuxtLoadingIndicator` in `app.vue`.
    const getLoadingIndicator = () =>
      nuxtApp.runWithContext(() => useLoadingIndicator())

    const loadFallbackIfNeeded = async (locale) => {
      if (locale !== 'en') {
        try {
          $i18n.fallbackLocale.value = 'en'
          await $i18n.loadLocaleMessages('en')
        } catch (error) {
          console.warn('Failed to load fallback locale messages:', error)
        }
      }
    }

    // Switching the language downloads the messages of the new locale, which can
    // take a while on a slow connection, so the progress bar is shown until
    // everything of the new locale has been loaded.
    let momentLocaleLoaded = null
    nuxtApp.hook('i18n:beforeLocaleSwitch', ({ newLocale }) => {
      // `initialSetup` can't be used to skip the first page load, because it's
      // never reset with the `no_prefix` strategy.
      if (import.meta.client && !nuxtApp.isHydrating) {
        getLoadingIndicator().start()
        // Started here, so that it downloads in parallel with the messages.
        momentLocaleLoaded = setMomentLocale(newLocale)
      }
    })
    nuxtApp.hook('i18n:localeSwitched', async ({ newLocale }) => {
      try {
        await Promise.all([
          momentLocaleLoaded || setMomentLocale(newLocale),
          loadFallbackIfNeeded(newLocale),
        ])
      } finally {
        momentLocaleLoaded = null
        if (import.meta.client) {
          getLoadingIndicator().finish()
        }
      }
    })

    await Promise.all([
      setMomentLocale($i18n.locale.value),
      loadFallbackIfNeeded($i18n.locale.value),
    ])
  },
})
