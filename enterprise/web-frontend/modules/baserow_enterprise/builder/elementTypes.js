import { ElementType } from '@baserow/modules/builder/elementTypes'
import AuthFormElement from '@baserow_enterprise/builder/components/elements/AuthFormElement'
import AuthFormElementForm from '@baserow_enterprise/builder/components/elements/AuthFormElementForm'
import { AfterLoginEvent } from '@baserow/modules/builder/eventTypes'

export class AuthFormElementType extends ElementType {
  static getType() {
    return 'auth_form'
  }

  get name() {
    return this.app.i18n.t('elementType.authForm')
  }

  get description() {
    return this.app.i18n.t('elementType.authFormDescription')
  }

  get iconClass() {
    return 'iconoir-log-in'
  }

  get component() {
    return AuthFormElement
  }

  get generalFormComponent() {
    return AuthFormElementForm
  }

  getEvents(element) {
    return [new AfterLoginEvent({ ...this.app })]
  }

  isInError({ builder, element }) {
    if (!element.user_source_id) {
      return true
    }
    const userSource = this.app.store.getters['userSource/getUserSourceById'](
      builder,
      element.user_source_id
    )
    if (!userSource) {
      return true
    }
    const userSourceType = this.app.$registry.get('userSource', userSource.type)
    const loginOptions = userSourceType.getLoginOptions(userSource)

    return Object.keys(loginOptions).length === 0
  }
}
