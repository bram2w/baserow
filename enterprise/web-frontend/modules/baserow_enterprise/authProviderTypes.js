import { AuthProviderType } from '@baserow/modules/core/authProviderTypes'

import SamlLoginAction from '@baserow_enterprise/components/admin/login/SamlLoginAction'
import AuthProviderItem from '@baserow_enterprise/components/admin/AuthProviderItem'
import SamlSettingsForm from '@baserow_enterprise/components/admin/forms/SamlSettingsForm'
import OAuth2SettingsForm from '@baserow_enterprise/components/admin/forms/OAuth2SettingsForm.vue'
import GitLabSettingsForm from '@baserow_enterprise/components/admin/forms/GitLabSettingsForm.vue'
import OpenIdConnectSettingsForm from '@baserow_enterprise/components/admin/forms/OpenIdConnectSettingsForm.vue'
import LoginButton from '@baserow_enterprise/components/admin/login/LoginButton.vue'

import PasswordAuthIcon from '@baserow/modules/core/assets/images/providers/Key.svg'
import SAMLIcon from '@baserow_enterprise/assets/images/providers/LockKey.svg'
import GoogleIcon from '@baserow_enterprise/assets/images/providers/Google.svg'
import FacebookIcon from '@baserow_enterprise/assets/images/providers/Facebook.svg'
import GitHubIcon from '@baserow_enterprise/assets/images/providers/GitHub.svg'
import GitLabIcon from '@baserow_enterprise/assets/images/providers/GitLab.svg'
import OpenIdIcon from '@baserow_enterprise/assets/images/providers/OpenID.svg'
import VerifiedProviderIcon from '@baserow_enterprise/assets/images/providers/VerifiedProviderIcon.svg'

export class PasswordAuthProviderType extends AuthProviderType {
  getType() {
    return 'password'
  }

  getIcon() {
    return PasswordAuthIcon
  }

  getName() {
    return this.app.i18n.t('authProviderTypes.password')
  }

  getProviderName(provider) {
    return this.getName()
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return null
  }

  getOrder() {
    return 1
  }
}

export class SamlAuthProviderType extends AuthProviderType {
  getType() {
    return 'saml'
  }

  getIcon() {
    return SAMLIcon
  }

  getVerifiedIcon() {
    return VerifiedProviderIcon
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
      acsUrl: authProviderType.acs_url,
      relayStateUrl: authProviderType.relay_state_url,
      ...populated,
    }
  }
}

export class GoogleAuthProviderType extends AuthProviderType {
  getType() {
    return 'google'
  }

  getIcon() {
    return GoogleIcon
  }

  getName() {
    return 'Google'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : `Google`
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class FacebookAuthProviderType extends AuthProviderType {
  getType() {
    return 'facebook'
  }

  getIcon() {
    return FacebookIcon
  }

  getName() {
    return 'Facebook'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class GitHubAuthProviderType extends AuthProviderType {
  getType() {
    return 'github'
  }

  getIcon() {
    return GitHubIcon
  }

  getName() {
    return 'GitHub'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return OAuth2SettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class GitLabAuthProviderType extends AuthProviderType {
  getType() {
    return 'gitlab'
  }

  getIcon() {
    return GitLabIcon
  }

  getName() {
    return 'GitLab'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return GitLabSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}

export class OpenIdConnectAuthProviderType extends AuthProviderType {
  getType() {
    return 'openid_connect'
  }

  getIcon() {
    return OpenIdIcon
  }

  getName() {
    return 'OpenID Connect'
  }

  getProviderName(provider) {
    return provider.name ? provider.name : this.getName()
  }

  getLoginButtonComponent() {
    return LoginButton
  }

  getAdminListComponent() {
    return AuthProviderItem
  }

  getAdminSettingsFormComponent() {
    return OpenIdConnectSettingsForm
  }

  getOrder() {
    return 50
  }

  populateLoginOptions(authProviderOption) {
    const loginOptions = super.populateLoginOptions(authProviderOption)
    return {
      ...loginOptions,
    }
  }

  populate(authProviderType) {
    const populated = super.populate(authProviderType)
    return {
      ...populated,
    }
  }
}
