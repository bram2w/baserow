<template>
  <div>
    <div v-if="view.filters.length === 0">
      <div class="filters__none">
        <div class="filters__none-title">
          {{ $t('viewFilterContext.noFilterTitle') }}
        </div>
        <div class="filters__none-description">
          {{ $t('viewFilterContext.noFilterText') }}
        </div>
      </div>
    </div>
    <ViewFieldConditionsForm
      :filters="view.filters"
      :disable-filter="disableFilter"
      :filter-type="view.filter_type"
      :fields="fields"
      :view="view"
      :read-only="readOnly"
      class="filters__items"
      @deleteFilter="deleteFilter($event)"
      @updateFilter="updateFilter($event)"
      @selectOperator="updateView(view, { filter_type: $event })"
    />
    <div v-if="!disableFilter" class="filters_footer">
      <a class="filters__add" @click.prevent="addFilter()">
        <i class="fas fa-plus"></i>
        {{ $t('viewFilterContext.addFilter') }}</a
      >
      <div v-if="view.filters.length > 0">
        <SwitchInput
          :value="view.filters_disabled"
          @input="updateView(view, { filters_disabled: $event })"
          >{{ $t('viewFilterContext.disableAllFilters') }}</SwitchInput
        >
      </div>
    </div>
  </div>
</template>

<script>
import { notifyIf } from '@baserow/modules/core/utils/error'
import ViewFieldConditionsForm from '@baserow/modules/database/components/view/ViewFieldConditionsForm'
import { hasCompatibleFilterTypes } from '@baserow/modules/database/utils/field'

export default {
  name: 'ViewFilterForm',
  components: {
    ViewFieldConditionsForm,
  },
  props: {
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    disableFilter: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    filterTypes() {
      return this.$registry.getAll('viewFilter')
    },
  },
  methods: {
    async addFilter(values) {
      try {
        const field = this.getFirstCompatibleField(this.fields)
        if (field === undefined) {
          await this.$store.dispatch('notification/error', {
            title: this.$t(
              'viewFilterContext.noCompatibleFilterTypesErrorTitle'
            ),
            message: this.$t(
              'viewFilterContext.noCompatibleFilterTypesErrorMessage'
            ),
          })
        } else {
          await this.$store.dispatch('view/createFilter', {
            field,
            view: this.view,
            values: {
              field: field.id,
            },
            emitEvent: false,
            readOnly: this.readOnly,
          })
          this.$emit('changed')
        }
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    getFirstCompatibleField(fields) {
      return fields
        .slice()
        .sort((a, b) => b.primary - a.primary)
        .find((field) => hasCompatibleFilterTypes(field, this.filterTypes))
    },
    async deleteFilter(filter) {
      try {
        await this.$store.dispatch('view/deleteFilter', {
          view: this.view,
          filter,
          readOnly: this.readOnly,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Updates a filter with the given values. Some data manipulation will also be done
     * because some filter types are not compatible with certain field types.
     */
    async updateFilter({ filter, values }) {
      try {
        await this.$store.dispatch('view/updateFilter', {
          filter,
          values,
          readOnly: this.readOnly,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    /**
     * Updates the view filter type. It will mark the view as loading because that
     * will also trigger the loading state of the second filter.
     */
    async updateView(view, values) {
      this.$store.dispatch('view/setItemLoading', { view, value: true })

      try {
        await this.$store.dispatch('view/update', {
          view,
          values,
          readOnly: this.readOnly,
        })
        this.$emit('changed')
      } catch (error) {
        notifyIf(error, 'view')
      }

      this.$store.dispatch('view/setItemLoading', { view, value: false })
    },
  },
}
</script>
