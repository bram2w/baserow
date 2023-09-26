<template>
  <table class="table-element">
    <thead>
      <tr class="table-element__header-row">
        <th class="table-element__header-cell">Column 1</th>
        <th class="table-element__header-cell">Column 2</th>
      </tr>
    </thead>
    <tbody>
      <tr class="table-element__row">
        <td class="table-element__cell">Value 1</td>
        <td class="table-element__cell">Value 2</td>
      </tr>
    </tbody>
  </table>
</template>

<script>
import element from '@baserow/modules/builder/mixins/element'

export default {
  name: 'TableElement',
  mixins: [element],
  props: {
    /**
     * @type {Object}
     * @property {int} data_source_id - The collection data source Id we want to
     *   display.
     * @property {Object} fields - The fields of the data source.
     */
    element: {
      type: Object,
      required: true,
    },
  },
}
</script>
