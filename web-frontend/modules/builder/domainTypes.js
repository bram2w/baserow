import { Registerable } from '@baserow/modules/core/registry'
import CustomDomainDetails from '@baserow/modules/builder/components/domain/CustomDomainDetails'
import CustomDomainForm from '@baserow/modules/builder/components/domain/CustomDomainForm'

export class DomainType extends Registerable {
  get name() {
    return null
  }

  get detailsComponent() {
    return null
  }
}

export class CustomDomainType extends DomainType {
  getType() {
    return 'custom'
  }

  get name() {
    return this.app.i18n.t('domainTypes.customName')
  }

  get detailsComponent() {
    return CustomDomainDetails
  }

  get formComponent() {
    return CustomDomainForm
  }
}
