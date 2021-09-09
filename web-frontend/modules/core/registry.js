/**
 * Only instances that are children of a Registerable can be registered into the
 * registry.
 */
export class Registerable {
  constructor({ app } = {}) {
    this.app = app
  }

  /**
   * Must return a string with the unique name, this must be the same as the
   * type used in the backend.
   */
  static getType() {
    throw new Error('The type of a registry must be set.')
  }

  getType() {
    return this.constructor.getType()
  }
}

/**
 * The registry is an class where Registerable instances can be registered under a
 * namespace. This is used for plugins to register extra functionality to Baserow. For
 * example the database plugin registers itself as an application to the core, but
 * it is also possible to register fields and views to the database plugin.
 */
export class Registry {
  constructor() {
    this.registry = {}
  }

  /**
   * Registers an empty namespace.
   */
  registerNamespace(namespace) {
    this.registry[namespace] = {}
  }

  /**
   * Registers a new Registerable object under the provided namespace in the registry.
   * If the namespace doesn't exist it will be created. It is common to register
   * instantiated classes here.
   */
  register(namespace, object) {
    if (!(object instanceof Registerable)) {
      throw new TypeError(
        'The registered object must be an instance of Registrable.'
      )
    }
    const type = object.getType()

    if (!Object.prototype.hasOwnProperty.call(this.registry, namespace)) {
      this.registry[namespace] = {}
    }
    this.registry[namespace][type] = object
  }

  /**
   * Un-registers a registered type from the provided namespace in the
   * registry. Throws an error if the registry does not exist. Returns true if the
   * type was found and deleted successfully, or false if the type did not exist in
   * the namespace.
   */
  unregister(namespace, type) {
    if (!Object.prototype.hasOwnProperty.call(this.registry, namespace)) {
      throw new Error(
        `The namespace ${namespace} is not found in the registry.`
      )
    }
    return delete this.registry[namespace][type]
  }

  /**
   * Returns a registered object with the given type in the provided namespace.
   */
  get(namespace, type) {
    if (!Object.prototype.hasOwnProperty.call(this.registry, namespace)) {
      throw new Error(
        `The namespace ${namespace} is not found in the registry.`
      )
    }
    if (!Object.prototype.hasOwnProperty.call(this.registry[namespace], type)) {
      throw new Error(
        `The type ${type} is not found under namespace ${namespace} in the registry.`
      )
    }
    return this.registry[namespace][type]
  }

  /**
   * Returns all the objects that are in the given namespace.
   */
  getAll(namespace) {
    if (!Object.prototype.hasOwnProperty.call(this.registry, namespace)) {
      throw new Error(
        `The namespace ${namespace} is not found in the registry.`
      )
    }
    return this.registry[namespace]
  }

  /**
   * Returns true if the object of the given type exists in the namespace.
   */
  exists(namespace, type) {
    if (!Object.prototype.hasOwnProperty.call(this.registry, namespace)) {
      return false
    }
    if (!Object.prototype.hasOwnProperty.call(this.registry[namespace], type)) {
      return false
    }
    return true
  }
}
