<template>
  <Modal ref="modal">
    <form @submit.prevent="create">
      <h2 v-if="primary !== undefined" class="box__title">
        {{ heading }}
      </h2>
      <Error :error="error"></Error>
      <RowEditModalField
        v-for="field in allFields"
        :key="'row-create-field-' + field.id"
        :ref="'field-' + field.id"
        :field="field"
        :row="row"
        :table="table"
        :read-only="false"
        @update="update"
        @field-updated="$emit('field-updated', $event)"
        @field-deleted="$emit('field-deleted')"
      ></RowEditModalField>
      <div class="actions">
        <div class="align-right">
          <button
            class="button button--large"
            :class="{ 'button--loading': loading }"
            :disabled="loading"
          >
            {{ $t('action.create') }}
          </button>
        </div>
      </div>
    </form>
  </Modal>
</template>

<script>
import Vue from 'vue'
import modal from '@baserow/modules/core/mixins/modal'
import error from '@baserow/modules/core/mixins/error'
import RowEditModalField from '@baserow/modules/database/components/row/RowEditModalField'

export default {
  name: 'RowCreateModal',
  components: {
    RowEditModalField,
  },
  mixins: [modal, error],
  props: {
    table: {
      type: Object,
      required: true,
    },
    primary: {
      type: Object,
      required: false,
      default: undefined,
    },
    fields: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      row: {},
      loading: false,
    }
  },
  computed: {
    allFields() {
      return [this.primary]
        .concat(this.fields)
        .slice()
        .sort((a, b) => a.order - b.order)
    },
    heading() {
      const name = `field_${this.primary.id}`
      if (Object.prototype.hasOwnProperty.call(this.row, name)) {
        return this.$registry
          .get('field', this.primary.type)
          .toHumanReadableString(this.primary, this.row[name])
      } else {
        return null
      }
    },
  },
  methods: {
    show(defaults = {}, ...args) {
      const row = {}
      this.allFields.forEach((field) => {
        const name = `field_${field.id}`
        const fieldType = this.$registry.get('field', field._.type.type)
        row[name] = fieldType.getNewRowValue(field)
      })
      Object.assign(row, defaults)
      Vue.set(this, 'row', row)
      return modal.methods.show.call(this, ...args)
    },
    update(event) {
      const name = `field_${event.field.id}`
      this.row[name] = event.value
    },
    create() {
      this.loading = true
      this.$emit('created', {
        row: this.row,
        callback: (error) => {
          if (error) {
            this.handleError(error)
          } else {
            this.hide()
          }
          this.loading = false
        },
      })
    },
  },
}
</script>
