import { Registerable } from '@baserow/modules/core/registry'
import ViewOwnershipRadioVue from './components/view/ViewOwnershipRadio.vue'

export class ViewOwnershipType extends Registerable {
  /**
   * A human readable name of the view ownership type.
   */
  getName() {
    return null
  }

  /**
   * A human readable name of the feature it belongs to.
   */
  getFeatureName() {
    return this.getName()
  }

  /**
   * The icon for the type in the form of CSS class.
   */
  getIconClass() {
    return null
  }

  /*
   * Radio component used in view ownership forms.
   */
  getRadioComponent() {
    return ViewOwnershipRadioVue
  }

  /**
   * Indicates if the view ownership type is disabled.
   */
  isDeactivated(groupId) {
    return false
  }

  /**
   * Text description when deactivated.
   */
  getDeactivatedText() {
    return null
  }

  /**
   * Show deactivated modal when selecting.
   */
  getDeactivatedModal() {
    return null
  }

  /**
   * The order in which groups of diff. view ownership
   * types appear in the list views.
   */
  getListViewTypeSort() {
    return 50
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      name: this.getName(),
    }
  }
}

export class CollaborativeViewOwnershipType extends ViewOwnershipType {
  static getType() {
    return 'collaborative'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('viewOwnershipType.collaborative')
  }

  getIconClass() {
    return 'fas fa-users'
  }

  isDeactivated(groupId) {
    return false
  }
}
