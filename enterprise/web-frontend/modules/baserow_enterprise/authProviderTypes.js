import { AuthProviderType } from '@baserow/modules/core/authProviderTypes'
import SamlLoginAction from '@baserow_enterprise/components/admin/login/SamlLoginAction'
import AuthProviderItem from '@baserow_enterprise/components/admin/AuthProviderItem'
import SamlSettingsForm from '@baserow_enterprise/components/admin/forms/SamlSettingsForm'

export class SamlAuthProviderType extends AuthProviderType {
  getType() {
    return 'saml'
  }

  getIconClass() {
    return 'fas fa-key'
  }

  getName() {
    return 'SSO SAML provider'
  }

  getProviderName(provider) {
    return `SSO SAML: ${provider.domain}`
  }

  getLoginActionComponent() {
    return SamlLoginAction
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return SamlSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      redirectUrl: authProviderOption.redirect_url,
      domainRequired: authProviderOption.domain_required,
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      isVerified: authProviderType.is_verified,
      metadata: authProviderType.metadata,
      ...populated,
    }
  }
}
