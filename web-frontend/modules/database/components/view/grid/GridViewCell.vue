<template functional>
  <div
    ref="wrapper"
    class="grid-view__column"
    :class="{
      'grid-view__column--matches-search':
        props.row._.matchSearch &&
        props.row._.fieldSearchMatches.includes(props.field.id.toString()),
    }"
    :style="data.style"
    @click="$options.methods.select($event, parent, props.field.id)"
  >
    <component
      :is="$options.methods.getFunctionalComponent(parent, props)"
      v-if="
        !parent.isCellSelected(props.field.id) &&
        // It could happen that the selected component needs to be alive in order to
        // finish a task. This is for example the case when still uploading files. The
        // alive list contains the field ids that must be kept alive. Once finished it
        // is removed from that list.
        !parent.alive.includes(props.field.id)
      "
      ref="unselectedField"
      :field="props.field"
      :value="props.row['field_' + props.field.id]"
      :state="props.state"
      :read-only="props.readOnly"
    />
    <component
      :is="$options.methods.getComponent(parent, props)"
      v-else
      ref="selectedField"
      :field="props.field"
      :value="props.row['field_' + props.field.id]"
      :selected="parent.isCellSelected(props.field.id)"
      :read-only="props.readOnly"
      @update="(...args) => $options.methods.update(listeners, props, ...args)"
      @edit="(...args) => $options.methods.edit(listeners, props, ...args)"
      @unselect="$options.methods.unselect(parent, props)"
      @selected="$options.methods.selected(listeners, props, $event)"
      @unselected="$options.methods.unselected(listeners, props, $event)"
      @selectPrevious="
        $options.methods.selectNext(listeners, props, 'previous')
      "
      @selectNext="$options.methods.selectNext(listeners, props, 'next')"
      @selectAbove="$options.methods.selectNext(listeners, props, 'above')"
      @selectBelow="$options.methods.selectNext(listeners, props, 'below')"
      @add-keep-alive="parent.addKeepAlive(props.field.id)"
      @remove-keep-alive="parent.removeKeepAlive(props.field.id)"
    />
  </div>
</template>

<script>
export default {
  methods: {
    /**
     * Returns the functional component related to the field type. Functional
     * components are much faster then regular components because they don't have a
     * state. Unselected cells renders this functional component to improve speed
     * because that will give the user a better experience. Once the user clicks on the
     * cell, it is replaced with a the real field component which has the ability to
     * change the data.
     */
    getFunctionalComponent(parent, props) {
      return parent.$registry
        .get('field', props.field.type)
        .getFunctionalGridViewFieldComponent()
    },
    /**
     * Returns the component related to the field type. This component will only be
     * rendered when the user has selected the cell. It will be used to edit the value.
     */
    getComponent(parent, props) {
      return parent.$registry
        .get('field', props.field.type)
        .getGridViewFieldComponent()
    },
    /**
     * If the grid field component emits an update event then this method will be
     * called which will add forward the event to the parent components which will
     * eventually update the value.
     */
    update(listeners, props, value, oldValue) {
      if (listeners.update) {
        listeners.update({
          row: props.row,
          field: props.field,
          value,
          oldValue,
        })
      }
    },
    /**
     * If the grid field components emits an edit event then the user has changed the
     * value without saving it yet. This is for example used to check in real time if
     * the value still matches the filters.
     */
    edit(listeners, props, value, oldValue) {
      if (listeners.edit) {
        listeners.edit({
          row: props.row,
          field: props.field,
          value,
          oldValue,
        })
      }
    },
    /**
     * When the user clicks on the cell it must be selected. We can only change that
     * state by calling the parent `selectCell` method.
     */
    select(event, parent, fieldId) {
      event.preventFieldCellUnselect = true
      parent.selectCell(fieldId)
    },
    /**
     * Called when the cell field type component needs to cell to be unselected.
     */
    unselect(parent, props) {
      if (parent.isCellSelected(props.field.id)) {
        parent.selectCell(-1, -1)
      }
    },
    /**
     * Called after the field type component is selected.
     */
    selected(listeners, props, event) {
      if (listeners.selected) {
        event.row = props.row
        event.field = props.field
        listeners.selected(event)
      }
    },
    /**
     * Called after the field type component is unselected.
     */
    unselected(listeners, props, event) {
      if (listeners.unselected) {
        event.row = props.row
        event.field = props.field
        listeners.unselected(event)
      }
    },
    /**
     * Called when the field type component want to select to next cell. This for
     * example happens when the user presses an arrow key.
     */
    selectNext(listeners, props, direction) {
      if (listeners['select-next']) {
        listeners['select-next']({
          row: props.row,
          field: props.field,
          direction,
        })
      }
    },
  },
}
</script>
