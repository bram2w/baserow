import { FormViewModeType } from '@baserow/modules/database/formViewModeTypes'
import PremiumModal from '@baserow_premium/components/PremiumModal'
import FormViewModeSurvey from '@baserow_premium/components/views/form/FormViewModeSurvey'
import FormViewModePreviewSurvey from '@baserow_premium/components/views/form/FormViewModePreviewSurvey'
import PremiumFeatures from '@baserow_premium/features'

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
    return 'iconoir-reports'
  }

  getDeactivatedText() {
    const { i18n } = this.app
    return i18n.t('formViewModeType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return PremiumModal
  }

  isDeactivated(workspaceId) {
    return !this.app.$hasFeature(PremiumFeatures.PREMIUM, workspaceId)
  }

  getFormComponent() {
    return FormViewModeSurvey
  }

  getPreviewComponent() {
    return FormViewModePreviewSurvey
  }
}
