import { FormViewModeType } from '@baserow/modules/database/formViewModeTypes'
import { PremiumPlugin } from '@baserow_premium/plugins'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import FormViewModeSurvey from '@baserow_premium/components/views/form/FormViewModeSurvey'
import FormViewModePreviewSurvey from '@baserow_premium/components/views/form/FormViewModePreviewSurvey'

export class FormViewSurveyModeType extends FormViewModeType {
  static getType() {
    return 'survey'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('formViewModeType.survey')
  }

  getDescription() {
    const { i18n } = this.app
    return i18n.t('formViewModeType.surveyDescription')
  }

  getIconClass() {
    return 'poll-h'
  }

  getDeactivatedText() {
    const { i18n } = this.app
    return i18n.t('formViewModeType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(groupId) {
    return !this.app.$registry
      .get('plugin', PremiumPlugin.getType())
      .activeLicenseHasPremiumFeatures(groupId)
  }

  getFormComponent() {
    return FormViewModeSurvey
  }

  getPreviewComponent() {
    return FormViewModePreviewSurvey
  }
}
