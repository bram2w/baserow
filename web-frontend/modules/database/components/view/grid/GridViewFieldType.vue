<template>
  <div
    class="grid-view__column"
    :class="{
      'grid-view__column--filtered':
        !view.filters_disabled &&
        view.filters.findIndex((filter) => filter.field === field.id) !== -1,
      'grid-view__column--sorted':
        view.sortings.findIndex((sort) => sort.field === field.id) !== -1,
    }"
    :style="{ width: width + 'px' }"
    @mousedown="startDragging($event, field)"
  >
    <div
      class="grid-view__description"
      :class="{ 'grid-view__description--loading': field._.loading }"
    >
      <div class="grid-view__description-icon">
        <i class="fas" :class="'fa-' + field._.type.iconClass"></i>
      </div>
      <div class="grid-view__description-name">
        <span ref="quickEditLink" @dblclick="handleQuickEdit()">
          {{ field.name }}
        </span>
      </div>
      <div v-if="field.error" class="grid-view__description-icon-error">
        <i v-tooltip="field.error" class="fas fa-exclamation-triangle"></i>
      </div>
      <a
        v-if="!readOnly && showFieldContext"
        ref="contextLink"
        class="grid-view__description-options"
        @click="$refs.context.toggle($refs.contextLink, 'bottom', 'right', 0)"
        @mousedown.stop
      >
        <i class="fas fa-caret-down"></i>
      </a>
      <FieldContext
        v-if="!readOnly"
        ref="context"
        :database="database"
        :table="table"
        :field="field"
        @update="$emit('refresh', $event)"
        @delete="$emit('refresh')"
      >
        <li
          v-if="
            !field.primary &&
            !readOnly &&
            $hasPermission(
              'database.table.create_field',
              table,
              database.group.id
            )
          "
        >
          <a
            ref="insertLeftLink"
            @click="
              $refs.insertFieldContext.toggle($refs.insertLeftLink, 'left')
            "
          >
            <i class="context__menu-icon fas fa-fw fa-arrow-left"></i>
            {{ $t('gridViewFieldType.insertLeft') }}
          </a>
        </li>
        <li
          v-if="
            !field.primary &&
            !readOnly &&
            $hasPermission(
              'database.table.create_field',
              table,
              database.group.id
            )
          "
        >
          <a
            ref="insertRightLink"
            @click="
              $refs.insertFieldContext.toggle($refs.insertRightLink, 'right')
            "
          >
            <i class="context__menu-icon fas fa-fw fa-arrow-right"></i>
            {{ $t('gridViewFieldType.insertRight') }}
          </a>
          <InsertFieldContext
            ref="insertFieldContext"
            :table="table"
            :from-field="field"
            @field-created="$emit('field-created', $event)"
            @move-field="moveField($event)"
          ></InsertFieldContext>
        </li>
        <li
          v-if="
            !readOnly &&
            $hasPermission(
              'database.table.field.duplicate',
              field,
              database.group.id
            )
          "
        >
          <a
            @click=";[$refs.duplicateFieldModal.toggle(), $refs.context.hide()]"
          >
            <i class="context__menu-icon fas fa-fw fa-clone"></i>
            {{ $t('gridViewFieldType.duplicate') }}
          </a>
          <DuplicateFieldModal
            ref="duplicateFieldModal"
            :table="table"
            :from-field="field"
            @field-created="$emit('field-created', $event)"
            @move-field="moveField($event)"
          ></DuplicateFieldModal>
        </li>
        <li />
        <li
          v-if="
            canFilter &&
            $hasPermission(
              'database.table.view.create_filter',
              view,
              database.group.id
            )
          "
        >
          <a @click="createFilter($event, view, field)">
            <i class="context__menu-icon fas fa-fw fa-filter"></i>
            {{ $t('gridViewFieldType.createFilter') }}
          </a>
        </li>
        <li
          v-if="
            getCanSortInView(field) &&
            $hasPermission(
              'database.table.view.create_sort',
              view,
              database.group.id
            )
          "
        >
          <a @click="createSort($event, view, field, 'ASC')">
            <i class="context__menu-icon fas fa-fw fa-sort-amount-down-alt"></i>
            {{ $t('gridViewFieldType.sortField') }}
            <template v-if="getSortIndicator(field, 0) === 'text'">{{
              getSortIndicator(field, 1)
            }}</template>
            <i
              v-if="getSortIndicator(field, 0) === 'icon'"
              class="fa"
              :class="'fa-' + getSortIndicator(field, 1)"
            ></i>
            <i class="fas fa-long-arrow-alt-right"></i>
            <template v-if="getSortIndicator(field, 0) === 'text'">{{
              getSortIndicator(field, 2)
            }}</template>
            <i
              v-if="getSortIndicator(field, 0) === 'icon'"
              class="fa"
              :class="'fa-' + getSortIndicator(field, 2)"
            ></i>
          </a>
        </li>
        <li
          v-if="
            getCanSortInView(field) &&
            $hasPermission(
              'database.table.view.create_sort',
              view,
              database.group.id
            )
          "
        >
          <a @click="createSort($event, view, field, 'DESC')">
            <i class="context__menu-icon fas fa-fw fa-sort-amount-down"></i>
            {{ $t('gridViewFieldType.sortField') }}
            <template v-if="getSortIndicator(field, 0) === 'text'">{{
              getSortIndicator(field, 2)
            }}</template>
            <i
              v-if="getSortIndicator(field, 0) === 'icon'"
              class="fa"
              :class="'fa-' + getSortIndicator(field, 2)"
            ></i>
            <i class="fas fa-long-arrow-alt-right"></i>
            <template v-if="getSortIndicator(field, 0) === 'text'">{{
              getSortIndicator(field, 1)
            }}</template>
            <i
              v-if="getSortIndicator(field, 0) === 'icon'"
              class="fa"
              :class="'fa-' + getSortIndicator(field, 1)"
            ></i>
          </a>
        </li>
        <li
          v-if="
            !field.primary &&
            canFilter &&
            $hasPermission(
              'database.table.view.update_field_options',
              view,
              database.group.id
            )
          "
        >
          <a @click="hide($event, view, field)">
            <i class="context__menu-icon fas fa-fw fa-eye-slash"></i>
            {{ $t('gridViewFieldType.hideField') }}
          </a>
        </li>
      </FieldContext>
      <GridViewFieldWidthHandle
        v-if="includeFieldWidthHandles"
        class="grid-view__description-width"
        :database="database"
        :grid="view"
        :field="field"
        :width="width"
        :read-only="
          readOnly ||
          !$hasPermission(
            'database.table.view.update_field_options',
            view,
            database.group.id
          )
        "
        :store-prefix="storePrefix"
      ></GridViewFieldWidthHandle>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'
import { notifyIf } from '@baserow/modules/core/utils/error'

import FieldContext from '@baserow/modules/database/components/field/FieldContext'
import InsertFieldContext from '@baserow/modules/database/components/field/InsertFieldContext'
import DuplicateFieldModal from '@baserow/modules/database/components/field/DuplicateFieldModal'
import GridViewFieldWidthHandle from '@baserow/modules/database/components/view/grid/GridViewFieldWidthHandle'
import gridViewHelpers from '@baserow/modules/database/mixins/gridViewHelpers'

export default {
  name: 'GridViewFieldType',
  components: {
    FieldContext,
    GridViewFieldWidthHandle,
    InsertFieldContext,
    DuplicateFieldModal,
  },
  mixins: [gridViewHelpers],
  props: {
    database: {
      type: Object,
      required: true,
    },
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
    includeFieldWidthHandles: {
      type: Boolean,
      required: false,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
  },
  data() {
    return {
      dragging: false,
    }
  },
  computed: {
    width() {
      return this.getFieldWidth(this.field.id)
    },
    canFilter() {
      const filters = Object.values(this.$registry.getAll('viewFilter'))
      for (const type in filters) {
        if (filters[type].fieldIsCompatible(this.field)) {
          return true
        }
      }
      return false
    },
    showFieldContext() {
      return (
        this.$hasPermission(
          'database.table.create_field',
          this.table,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.create_filter',
          this.view,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.create_sort',
          this.view,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.view.update_field_options',
          this.view,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.field.duplicate',
          this.field,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.field.update',
          this.field,
          this.database.group.id
        ) ||
        this.$hasPermission(
          'database.table.field.delete',
          this.field,
          this.database.group.id
        )
      )
    },
  },
  beforeCreate() {
    this.$options.computed = {
      ...(this.$options.computed || {}),
      ...mapGetters({
        fieldOptions:
          this.$options.propsData.storePrefix + 'view/grid/getAllFieldOptions',
      }),
    }
  },
  methods: {
    moveField($event) {
      this.$emit('move-field', $event)
      this.$refs.context.hide()
    },
    async handleQuickEdit() {
      if (this.readOnly) return false
      await this.$refs.context.toggle(
        this.$refs.quickEditLink,
        'bottom',
        'left',
        0
      )
      this.$refs.context.showUpdateFieldContext()
    },
    quickEditField($event) {
      this.$emit('updated', $event)
      this.$refs.context.hide()
    },
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
          },
        })
        this.$emit('refresh')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    async createSort(event, view, field, order) {
      // Prevent the event from propagating to the body so that it does not close the
      // view filter context menu right after it has been opened. This is due to the
      // click outside event that is fired there.
      event.stopPropagation()
      event.preventDefault()
      this.$refs.context.hide()

      const sort = view.sortings.find((sort) => sort.field === this.field.id)
      const values = {
        field: field.id,
        order,
      }

      try {
        if (sort === undefined) {
          await this.$store.dispatch('view/createSort', {
            view,
            field,
            values,
          })
        } else {
          await this.$store.dispatch('view/updateSort', {
            sort,
            values,
          })
        }

        this.$emit('refresh')
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    async hide(event, view, field) {
      try {
        await this.$store.dispatch(
          this.storePrefix + 'view/grid/updateFieldOptionsOfField',
          {
            field,
            values: { hidden: true },
            oldValues: { hidden: false },
            readOnly: !this.$hasPermission(
              'database.table.view.update_field_options',
              this.view,
              this.database.group.id
            ),
          }
        )
      } catch (error) {
        notifyIf(error, 'view')
      }
    },
    startDragging(event, field) {
      this.$emit('dragging', { field, event })
    },
    getSortIndicator(field, index) {
      return this.$registry
        .get('field', field.type)
        .getSortIndicator(field, this.$registry)[index]
    },
    getCanSortInView(field) {
      return this.$registry.get('field', field.type).getCanSortInView(field)
    },
  },
}
</script>
