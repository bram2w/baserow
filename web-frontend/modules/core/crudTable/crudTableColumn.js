/**
 * A column specification used by CrudTable to render your column of data.
 *
 * @param {string} key A unique key for this column which must be present in the
 * row object returned by the service provided to CrudTable.
 * @param {string} header The display text shown in the columns header.
 * @param cellComponent The cell component class used to render a cell of this column,
 * crudTable will listen to 'edit-row' (expected to emit a single updated row
 * object) and
 * 'delete-row' (expected to emit an updated row) events from this cell and
 * update the rows accordingly. CrudTable will pass two props to this component, the
 * column which is this object and the specific row returned by the service. Finally
 * any listeners defined on the CrudTable itself will be passed through to all
 * instances of this cellComponent.
 * @param {int} widthPerc The width which the table cell header should be limited to.
 * @param {boolean} sortable Whether this column is sortable.
 * @param {object} additionalProps Any additional props to pass to the cellComponent.
 */
export default class CrudTableColumn {
  constructor(
    key,
    header,
    cellComponent,
    sortable = false,
    stickyLeft = false,
    stickyRight = false,
    additionalProps = {},
    widthPerc = '',
    helpText = null
  ) {
    this.key = key
    this._header = header
    this.cellComponent = cellComponent
    this.sortable = sortable
    this.stickyLeft = stickyLeft
    this.stickyRight = stickyRight
    this.additionalProps = additionalProps
    this.widthPerc = widthPerc
    this.helpText = helpText
  }

  get header() {
    if (typeof this._header === 'function') {
      return this._header()
    }
    return this._header
  }
}
