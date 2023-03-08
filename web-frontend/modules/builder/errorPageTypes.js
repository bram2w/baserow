import { ErrorPageType } from '@baserow/modules/core/errorPageTypes'
import PublicSiteErrorPage from '@baserow/modules/builder/components/PublicSiteErrorPage'

export class PublicSiteErrorPageType extends ErrorPageType {
  getComponent() {
    return PublicSiteErrorPage
  }

  isApplicable() {
    return this.app.context.route.name === 'application-builder-page'
  }

  static getType() {
    return 'publicSite'
  }

  getOrder() {
    return 10
  }
}
