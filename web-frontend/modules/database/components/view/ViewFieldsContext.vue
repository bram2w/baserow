<template>
  <Context ref="context" class="hidings" @shown="shown()">
    <div class="hidings__head">
      <div v-if="allowCoverImageField" class="control hidings__cover">
        <label class="control__label control__label--small">{{
          $t('viewFieldsContext.coverField')
        }}</label>
        <div class="control__elements">
          <Dropdown
            :value="coverImageField"
            :disabled="
              !$hasPermission(
                'database.table.view.update',
                view,
                database.group.id
              )
            "
            @input="
              coverImageField !== $event &&
                $emit('update-cover-image-field', $event)
            "
          >
            <DropdownItem
              :name="$t('viewFieldsContext.noCover')"
              :value="null"
            ></DropdownItem>
            <DropdownItem
              v-for="fileField in fileFields"
              :key="fileField.id"
              :icon="fileField._.type.iconClass"
              :name="fileField.name"
              :value="fileField.id"
            ></DropdownItem>
          </Dropdown>
        </div>
      </div>
      <div class="hidings__search">
        <i class="hidings__search-icon fas fa-search"></i>
        <input
          ref="search"
          v-model="query"
          type="text"
          :placeholder="$t('viewFieldsContext.search')"
          class="hidings__search-input"
        />
      </div>
    </div>
    <div v-auto-overflow-scroll class="hidings__body">
      <ul class="hidings__list margin-bottom-0">
        <li
          v-for="field in filteredFields"
          :key="field.id"
          v-sortable="{
            id: field.id,
            update: order,
            handle: '[data-field-handle]',
          }"
          class="hidings__item"
        >
          <a class="hidings__item-handle" data-field-handle></a>
          <SwitchInput
            v-if="allowHidingFields"
            :value="!isHidden(field.id)"
            @input="updateFieldOptionsOfField(field, { hidden: !$event })"
          >
            <i
              class="fas fa-fw switch__icon"
              :class="'fa-' + field._.type.iconClass"
            ></i>
            <span>{{ field.name }}</span>
          </SwitchInput>
          <div v-else class="hidings__item-name">
            <i
              class="fas fa-fw switch__icon"
              :class="'fa-' + field._.type.iconClass"
            ></i>
            <span>{{ field.name }}</span>
          </div>
        </li>
      </ul>
    </div>
    <div v-if="allowHidingFields" v-show="query === ''" class="hidings__footer">
      <button
        class="button button--ghost hidings__footer-button"
        @click="!noneSelected && updateAllFieldOptions({ hidden: true })"
      >
        {{ $t('viewFieldsContext.hideAll') }}
      </button>
      <button
        class="button button--ghost"
        @click="!allSelected && updateAllFieldOptions({ hidden: false })"
      >
        {{ $t('viewFieldsContext.showAll') }}
      </button>
    </div>
  </Context>
</template>

<script>
import { mapGetters } from 'vuex'
import { escapeRegExp } from '@baserow/modules/core/utils/string'
import context from '@baserow/modules/core/mixins/context'
import { clone } from '@baserow/modules/core/utils/object'
import { FileFieldType } from '@baserow/modules/database/fieldTypes'
import { sortFieldsByOrderAndIdFunction } from '@baserow/modules/database/utils/view'

export default {
  name: 'ViewFieldsContext',
  mixins: [context],
  props: {
    database: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fieldOptions: {
      type: Object,
      required: true,
    },
    coverImageField: {
      required: false,
      default: null,
      validator: (prop) => typeof prop === 'number' || prop === null,
    },
    allowCoverImageField: {
      type: Boolean,
      required: false,
      default: false,
    },
    allowHidingFields: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  data() {
    return {
      query: '',
    }
  },
  computed: {
    noneSelected() {
      for (const i in this.fields) {
        if (!this.isHidden(this.fields[i].id)) {
          return false
        }
      }
      return true
    },
    allSelected() {
      for (const i in this.fields) {
        if (this.isHidden(this.fields[i].id)) {
          return false
        }
      }
      return true
    },
    filteredFields() {
      const query = this.query

      return this.fields
        .filter((field) => {
          const regex = new RegExp('(' + escapeRegExp(query) + ')', 'i')
          return field.name.match(regex)
        })
        .sort(sortFieldsByOrderAndIdFunction(this.fieldOptions))
    },
    fileFields() {
      const type = FileFieldType.getType()
      return this.fields.filter((field) => field.type === type)
    },
    ...mapGetters({
      allFields: 'field/getAll',
    }),
  },
  methods: {
    order(order, oldOrder) {
      this.$emit('update-order', {
        order: [this.allFields[0].id, ...order], // Add primary field first
        oldOrder,
      })
    },
    updateAllFieldOptions(values) {
      const newFieldOptions = {}
      const oldFieldOptions = clone(this.fieldOptions)
      this.fields.forEach((field) => {
        newFieldOptions[field.id] = values
      })

      this.$emit('update-all-field-options', {
        newFieldOptions,
        oldFieldOptions,
      })
    },
    updateFieldOptionsOfField(field, values) {
      this.$emit('update-field-options-of-field', {
        field,
        values,
        oldValues: { hidden: this.fieldOptions[field.id].hidden },
      })
    },
    isHidden(fieldId) {
      const exists = Object.prototype.hasOwnProperty.call(
        this.fieldOptions,
        fieldId
      )
      return exists ? this.fieldOptions[fieldId].hidden : false
    },
    shown() {
      this.query = ''
      this.$nextTick(() => {
        this.$refs.search.focus()
      })
    },
  },
}
</script>
