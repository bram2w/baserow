<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('tableElementForm.dataSource') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.data_source_id" :show-search="false">
          <DropdownItem
            v-for="dataSource in availableDataSources"
            :key="dataSource.id"
            :name="dataSource.name"
            :value="dataSource.id"
          />
        </Dropdown>
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  name: 'TableElementForm',
  components: {},
  mixins: [form],
  inject: ['page'],
  data() {
    return {
      values: {
        data_source_id: null,
        fields: [],
      },
    }
  },
  computed: {
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    availableDataSources() {
      return this.dataSources.filter(
        (dataSource) =>
          dataSource.type &&
          this.$registry.get('service', dataSource.type).isCollection
      )
    },
  },
}
</script>
