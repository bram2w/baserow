<template>
  <form @submit.prevent>
    <FormGroup
      :label="$t('tableElementForm.dataSource')"
      small-label
      required
      class="margin-bottom-2"
    >
      <div class="control__elements">
        <Dropdown v-model="values.data_source_id" :show-search="false">
          <DropdownItem
            v-for="dataSource in dataSources"
            :key="dataSource.id"
            :name="dataSource.name"
            :value="dataSource.id"
          />
        </Dropdown>
      </div>
    </FormGroup>
  </form>
</template>

<script>
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'RefreshDataSourceWorkflowActionForm',
  mixins: [elementForm],
  props: {
    workflowAction: {
      type: Object,
      required: false,
      default: null,
    },
  },
  data() {
    return {
      allowedValues: ['data_source_id'],
      values: {
        data_source_id: null,
      },
    }
  },
  computed: {
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
  },
}
</script>
