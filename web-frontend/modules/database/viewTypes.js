import { Registerable } from '@baserow/modules/core/registry'
import ViewForm from '@baserow/modules/database/components/view/ViewForm'
import GridView from '@baserow/modules/database/components/view/grid/GridView'

export class ViewType extends Registerable {
  /**
   * The font awesome 5 icon name that is used as convenience for the user to
   * recognize certain view types. If you for example want the database
   * icon, you must return 'database' here. This will result in the classname
   * 'fas fa-database'.
   */
  getIconClass() {
    return null
  }

  /**
   * A human readable name of the view type.
   */
  getName() {
    return null
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()

    if (this.type === null) {
      throw new Error('The type name of a view type must be set.')
    }
    if (this.iconClass === null) {
      throw new Error('The icon class of a view type must be set.')
    }
    if (this.name === null) {
      throw new Error('The name of a view type must be set.')
    }
  }

  /**
   * The form component that will be rendered when creating a new instance of
   * this view type. By default the ViewForm component is returned, but this
   * only contains a name field. If custom fields are required upon creating
   * they can be added by replacing this component with a custom oone.
   */
  getViewFormComponent() {
    return ViewForm
  }

  /**
   * Should return the component that will actually display the view.
   */
  getComponent() {
    throw new Error('Not implement error. This view should return a component.')
  }

  /**
   * Should return the component that will be displayed in the header when the
   * view is selected. Extra options like filters and sorting could be added
   * here.
   */
  getHeaderComponent() {
    return null
  }

  /**
   * Every time a fresh view object is fetched from the backend, it will be
   * populated, this is the moment to update some values. Because each view type
   * can have unique properties, they might need to be populated. This method
   * can be overwritten in order the populate the correct values.
   */
  populate(view) {
    return view
  }

  /**
   * The fetch method is called inside the asyncData function when the table page
   * loads with a selected view. It is possible to fill some stores serverside here.
   */
  fetch() {}

  /**
   * Method that is called when a field has been created. This can be useful to
   * maintain data integrity for example to add the field to the grid view store.
   */
  fieldCreated(context, table, field, fieldType) {}

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
    }
  }
}

export class GridViewType extends ViewType {
  static getType() {
    return 'grid'
  }

  getIconClass() {
    return 'th'
  }

  getName() {
    return 'Grid'
  }

  getComponent() {
    return GridView
  }

  async fetch({ store }, view) {
    await store.dispatch('view/grid/fetchInitial', { gridId: view.id })
  }

  fieldCreated({ dispatch }, table, field, fieldType) {
    const value = fieldType.getEmptyValue(field)
    dispatch('view/grid/addField', { field, value }, { root: true })
  }
}
