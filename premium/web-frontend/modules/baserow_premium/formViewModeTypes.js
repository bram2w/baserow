import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import { FormViewModeType } from '@baserow/modules/database/formViewModeTypes'
import PremiumFeatures from '@baserow_premium/features'
import { FormSurveyModePaidFeature } from '@baserow_premium/paidFeatures'

const FormViewModeSurvey = lazyComponent(
  () => import('@baserow_premium/components/views/form/FormViewModeSurvey')
)
const FormViewModePreviewSurvey = lazyComponent(
  () =>
    import('@baserow_premium/components/views/form/FormViewModePreviewSurvey')
)
const PaidFeaturesModal = lazyComponent(
  () => import('@baserow_premium/components/PaidFeaturesModal')
)

export class FormViewSurveyModeType extends FormViewModeType {
  static getType() {
    return 'survey'
  }

  getName() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.survey')
  }

  getDescription() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.surveyDescription')
  }

  getIconClass() {
    return 'iconoir-reports'
  }

  getDeactivatedText() {
    const { $i18n } = this.app
    return $i18n.t('formViewModeType.onlyForPremium')
  }

  getDeactivatedClickModal() {
    return [
      PaidFeaturesModal,
      { 'initial-selected-type': FormSurveyModePaidFeature.getType() },
    ]
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
