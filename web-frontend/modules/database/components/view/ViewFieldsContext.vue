<template>
  <Context ref="context" class="hidings" @shown="shown()">
    <div class="hidings__head">
      <div class="hidings__search">
        <i class="hidings__search-icon fas fa-search"></i>
        <input
          ref="search"
          v-model="query"
          type="text"
          placeholder="Search fields"
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
            enabled: !readOnly,
            id: field.id,
            update: order,
            handle: '[data-field-handle]',
          }"
          class="hidings__item"
        >
          <a
            v-show="!readOnly"
            class="hidings__item-handle"
            data-field-handle
          ></a>
          <SwitchInput
            :value="!isHidden(field.id)"
            :disabled="readOnly"
            @input="updateFieldOptionsOfField(field, { hidden: !$event })"
          >
            <i
              class="fas fa-fw switch__icon"
              :class="'fa-' + field._.type.iconClass"
            ></i>
            <span>{{ field.name }}</span>
          </SwitchInput>
        </li>
      </ul>
    </div>
    <div v-if="!readOnly" v-show="query === ''" class="hidings__footer">
      <button
        class="button button--ghost hidings__footer-button"
        @click="!noneSelected && updateAllFieldOptions({ hidden: true })"
      >
        {{ $t('gridViewHideContext.hideAll') }}
      </button>
      <button
        class="button button--ghost"
        @click="!allSelected && updateAllFieldOptions({ hidden: false })"
      >
        {{ $t('gridViewHideContext.showAll') }}
      </button>
    </div>
  </Context>
</template>

<script>
import { escapeRegExp } from '@baserow/modules/core/utils/string'
import context from '@baserow/modules/core/mixins/context'
import { clone } from '@baserow/modules/core/utils/object'
import { maxPossibleOrderValue } from '@baserow/modules/database/viewTypes'

export default {
  name: 'ViewFieldsContext',
  mixins: [context],
  props: {
    fields: {
      type: Array,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    fieldOptions: {
      type: Object,
      required: true,
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
        .sort((a, b) => {
          const orderA = this.fieldOptions[a.id]
            ? this.fieldOptions[a.id].order
            : maxPossibleOrderValue
          const orderB = this.fieldOptions[b.id]
            ? this.fieldOptions[b.id].order
            : maxPossibleOrderValue

          // First by order.
          if (orderA > orderB) {
            return 1
          } else if (orderA < orderB) {
            return -1
          }

          // Then by id.
          if (a.id < b.id) {
            return -1
          } else if (a.id > b.id) {
            return 1
          } else {
            return 0
          }
        })
    },
  },
  methods: {
    order(order, oldOrder) {
      this.$emit('update-order', { order, oldOrder })
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

<i18n>
{
  "en":{
    "gridViewHideContext": {
      "hideAll": "Hide all",
      "showAll": "Show all"
    }
  },
  "fr":{
    "gridViewHideContext": {
      "hideAll": "Masquer tout",
      "showAll": "Afficher tout"
    }
  }
}
</i18n>
