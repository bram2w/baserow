<template>
  <div class="kanban-view__stacked-by">
    <div class="kanban-view__stacked-by-title">
      {{ $t('kanbanViewStakedBy.title') }}
    </div>
    <div class="kanban-view__stacked-by-description">
      {{ $t('kanbanViewStakedBy.chooseField') }}
    </div>
    <Radio
      v-for="field in singleSelectFields"
      :key="field.id"
      v-model="singleSelectField"
      :value="field.id"
      :loading="loading && field.id === singleSelectField"
      :disabled="loading || readOnly"
      @input="update"
      >{{ field.name }}</Radio
    >
    <div v-if="!readOnly" class="margin-top-2">
      <a
        ref="createFieldContextLink"
        class="margin-right-auto"
        @click="$refs.createFieldContext.toggle($refs.createFieldContextLink)"
      >
        <i class="fas fa-plus"></i>
        {{ $t('kanbanViewStakedBy.addSelectField') }}
      </a>
      <CreateFieldContext
        ref="createFieldContext"
        :table="table"
        :forced-type="forcedFieldType"
      ></CreateFieldContext>
    </div>
  </div>
</template>

<script>
import kanbanViewHelper from '@baserow_premium/mixins/kanbanViewHelper'
import { SingleSelectFieldType } from '@baserow/modules/database/fieldTypes'
import CreateFieldContext from '@baserow/modules/database/components/field/CreateFieldContext'

export default {
  name: 'KanbanViewStackedBy',
  components: { CreateFieldContext },
  mixins: [kanbanViewHelper],
  props: {
    table: {
      type: Object,
      required: true,
    },
    view: {
      type: Object,
      required: true,
    },
    fields: {
      type: Array,
      required: true,
    },
    primary: {
      type: Object,
      required: true,
    },
    readOnly: {
      type: Boolean,
      required: true,
    },
    includeFieldOptionsOnRefresh: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      loading: false,
      singleSelectField: this.view.single_select_field,
    }
  },
  computed: {
    singleSelectFields() {
      const allFields = [this.primary].concat(this.fields)
      const singleSelectFieldType = SingleSelectFieldType.getType()
      return allFields.filter((field) => field.type === singleSelectFieldType)
    },
    forcedFieldType() {
      return SingleSelectFieldType.getType()
    },
  },
  watch: {
    'view.single_select_field'(value) {
      this.singleSelectField = value
    },
  },
  methods: {
    async update(value) {
      this.loading = true
      await this.updateKanban({
        single_select_field: value,
      })
      this.$emit('refresh', {
        callback: () => {
          this.loading = false
        },
        includeFieldOptions: this.includeFieldOptionsOnRefresh,
      })
    },
  },
}
</script>
