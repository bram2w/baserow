import { Registerable } from '@baserow/modules/core/registry'
import ViewForm from '@baserow/modules/database/components/view/ViewForm'
import GridView from '@baserow/modules/database/components/view/grid/GridView'
import GridViewHeader from '@baserow/modules/database/components/view/grid/GridViewHeader'

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

  /**
   * Indicates whether it is possible to filter the rows. If true the filter context
   * menu is added to the header.
   */
  canFilter() {
    return true
  }

  /**
   * Indicates whether it is possible to sort the rows. If true the sort context menu
   * is added to the header.
   */
  canSort() {
    return true
  }

  constructor() {
    super()
    this.type = this.getType()
    this.iconClass = this.getIconClass()
    this.name = this.getName()
    this.canFilter = this.canFilter()
    this.canSort = this.canSort()

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
   * Should refresh the data inside a few. This is method could be called when a filter
   * or sort has been changed or when a field is updated or deleted. It should keep the
   * state as much the same as it was before. So for example the scroll offset should
   * stay the same if possible.
   */
  refresh() {}

  /**
   * Method that is called when a field has been created. This can be useful to
   * maintain data integrity for example to add the field to the grid view store.
   */
  fieldCreated(context, table, field, fieldType) {}

  /**
   * Method that is called when a field has been changed. This can be useful to
   * maintain data integrity by updating the values.
   */
  fieldUpdated(context, field, oldField, fieldType) {}

  /**
   * Event that is called when a row is created from an outside source, so for example
   * via a real time event by another user. It can be used to check if data in an store
   * needs to be updated.
   */
  rowCreated(context, tableId, rowValues) {}

  /**
   * Event that is called when a row is updated from an outside source, so for example
   * via a real time event by another user. It can be used to check if data in an store
   * needs to be updated.
   */
  rowUpdated(context, tableId, rowValues) {}

  /**
   * Event that is called when a row is deleted from an outside source, so for example
   * via a real time event by another user. It can be used to check if data in an store
   * needs to be updated.
   */
  rowDeleted(context, tableId, rowId) {}

  /**
   * @return object
   */
  serialize() {
    return {
      type: this.type,
      iconClass: this.iconClass,
      name: this.name,
      canFilter: this.canFilter,
      canSort: this.canSort,
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

  getHeaderComponent() {
    return GridViewHeader
  }

  getComponent() {
    return GridView
  }

  async fetch({ store }, view) {
    await store.dispatch('view/grid/fetchInitial', { gridId: view.id })
  }

  async refresh({ store }, view) {
    await store.dispatch('view/grid/refresh', { gridId: view.id })
  }

  async fieldCreated({ dispatch }, table, field, fieldType) {
    const value = fieldType.getEmptyValue(field)
    await dispatch('view/grid/addField', { field, value }, { root: true })
    await dispatch(
      'view/grid/setFieldOptionsOfField',
      {
        field,
        // The default values should be the same as in the `GridViewFieldOptions`
        // model in the backend to stay consistent.
        values: {
          width: 200,
          hidden: false,
        },
      },
      { root: true }
    )
  }

  isCurrentView(store, tableId) {
    const table = store.getters['table/getSelected']
    const grid = store.getters['view/getSelected']
    return (
      table.id === tableId &&
      Object.prototype.hasOwnProperty.call(grid, 'type') &&
      grid.type === GridViewType.getType()
    )
  }

  rowCreated({ store }, tableId, rowValues) {
    if (this.isCurrentView(store, tableId)) {
      store.dispatch('view/grid/forceCreate', {
        view: store.getters['view/getSelected'],
        fields: store.getters['field/getAll'],
        primary: store.getters['field/getPrimary'],
        values: rowValues,
        getScrollTop: () => store.getters['view/grid/getScrollTop'],
      })
    }
  }

  rowUpdated({ store }, tableId, rowValues) {
    if (this.isCurrentView(store, tableId)) {
      store.dispatch('view/grid/forceUpdate', {
        view: store.getters['view/getSelected'],
        fields: store.getters['field/getAll'],
        primary: store.getters['field/getPrimary'],
        values: rowValues,
        getScrollTop: () => store.getters['view/grid/getScrollTop'],
      })
    }
  }

  rowDeleted({ store }, tableId, rowId) {
    if (this.isCurrentView(store, tableId)) {
      const row = { id: rowId }
      store.dispatch('view/grid/forceDelete', {
        grid: store.getters['view/getSelected'],
        row,
        getScrollTop: () => store.getters['view/grid/getScrollTop'],
      })
    }
  }
}
