<template>
  <div
    class="grid-view__column"
    :class="{
      'grid-view__column--filtered':
        view.filters.findIndex((filter) => filter.field === field.id) !== -1,
    }"
  >
    <div
      class="grid-view__description"
      :class="{ 'grid-view__description--loading': field._.loading }"
    >
      <div class="grid-view__description-icon">
        <i class="fas" :class="'fa-' + field._.type.iconClass"></i>
      </div>
      <div class="grid-view__description-name">{{ field.name }}</div>
      <a
        ref="contextLink"
        class="grid-view__description-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
      >
        <i class="fas fa-caret-down"></i>
      </a>
      <FieldContext ref="context" :table="table" :field="field">
        <li v-if="canFilter">
          <a
            class="grid-view__description-options"
            @click="createFilter($event, view, field)"
          >
            <i class="context__menu-icon fas fa-fw fa-filter"></i>
            Create filter
          </a>
        </li>
      </FieldContext>
      <slot></slot>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import FieldContext from '@baserow/modules/database/components/field/FieldContext'

export default {
  name: 'GridViewFieldType',
  components: { FieldContext },
  props: {
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    field: {
      type: Object,
      required: true,
    },
  },
  computed: {
    canFilter() {
      const filters = Object.values(this.$registry.getAll('viewFilter'))
      for (const type in filters) {
        if (filters[type].compatibleFieldTypes.includes(this.field.type)) {
          return true
        }
      }
      return false
    },
  },
  methods: {
    async createFilter(event, view, field) {
      // Prevent the event from propagating to the body so that it does not close the
      // view filter context menu right after it has been opened. This is due to the
      // click outside event that is fired there.
      event.stopPropagation()
      event.preventDefault()
      this.$refs.context.hide()

      try {
        await this.$store.dispatch('view/createFilter', {
          view,
          field,
          values: {
            field: field.id,
            value: '',
          },
        })
        this.$emit('refresh')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
  },
}
</script>
