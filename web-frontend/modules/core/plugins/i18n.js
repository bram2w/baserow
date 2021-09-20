import moment from '@baserow/modules/core/moment'

export default function ({ app }) {
  // Set moment locale on load
  moment.locale(app.i18n.locale)

  app.i18n.onLanguageSwitched = (oldLocale, newLocale) => {
    // Update moment locale on language switch
    moment.locale(newLocale)
  }
}
