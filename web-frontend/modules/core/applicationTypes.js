import ApplicationForm from '@baserow/modules/core/components/application/ApplicationForm'

/**
 * The application type base class that can be extended when creating a plugin
 * for the frontend.
 */
export class ApplicationType {
  /**
   * Must return a string with the unique name, this must be the same as the
   * type used in the backend.
   */
  getType() {
    return null
  }

  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize certain application types. If you for example want the database
   * icon, you must return 'database' here. This will result in the classname
   * 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the application type.
   */
  getName() {
    return null
  }

  /**
   * Must return the route name where the application can navigate to when the
   * application is selected.
   */
  getRouteName() {
    return null
  }

  /**
   * The form component that will be rendered when creating a new instance of
   * this application. By default the ApplicationForm component is returned, but
   * this only contains a name field. If custom fields are required upon
   * creating they can be added with this component.
   */
  getApplicationFormComponent() {
    return ApplicationForm
  }

  /**
   * The sidebar component that will be rendered when an application instance
   * is selected. By default no component will rendered. This could be used for
   * example to render a list of tables that belong to a database.
   */
  getSelectedSidebarComponent() {
    return null
  }

  constructor() {
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()
    this.routeName = this.getRouteName()

    if (this.type === null) {
      throw new Error('The type name of an application type must be set.')
    }
    if (this.iconClass === null) {
      throw new Error('The icon class of an application type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of an application type must be set.')
    }
  }

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
      routeName: this.routeName,
      hasSelectedSidebarComponent: this.getSelectedSidebarComponent() !== null,
    }
  }

  /**
   * Every time a fresh application object is fetched from the backend, it will
   * be populated, this is the moment to update some values. Because each
   * application can have unique properties, they might need to be populated.
   * This method can be overwritten in order the populate the correct values.
   */
  populate(application) {
    return application
  }

  /**
   * When an application is deleted it could be that an action should be taken,
   * like redirect the user to another page. This method is called when application
   * of this type is deleted.
   */
  delete(application, context) {}

  /**
   *
   */
  clearChildrenSelected(application) {}
}
