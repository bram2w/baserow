/**
 * This might look like something that belongs in a registry, but it does not.
 *
 * There is no point in making these accessible to plugin writers so there is no
 * registry required.
 */
export class Event {
  constructor({ i18n }) {
    this.$i18n = i18n
  }

  static getType() {
    throw new Error('getType needs to be implemented')
  }

  getType() {
    return this.constructor.getType()
  }

  get label() {
    return null
  }

  fire(eventContext) {
    console.log(`Fired an event of type: "${this.getType()}"`)
  }
}

export class ClickEvent extends Event {
  static getType() {
    return 'click'
  }

  get label() {
    return this.$i18n.t('eventTypes.clickLabel')
  }
}
