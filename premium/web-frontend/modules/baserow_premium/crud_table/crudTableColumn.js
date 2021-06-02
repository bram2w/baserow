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
 * @param {string} minWidth A valid min parameter to the css minmax(HERE,) function
 * used to construct CrudTable's css grid column templates.
 * @param {string} maxWidth A valid max parameter to the css minmax(,HERE) function to
 * construct CrudTable's css grid column templates.
 * @param {boolean} sortable Whether this column is sortable.
 */
export default class CrudTableColumn {
  constructor(key, header, cellComponent, minWidth, maxWidth, sortable) {
    this.key = key
    this.header = header
    this.cellComponent = cellComponent
    this.minWidth = minWidth
    this.maxWidth = maxWidth
    this.sortable = sortable
  }
}
