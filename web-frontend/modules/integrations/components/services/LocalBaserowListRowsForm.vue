<template>
  <form @submit.prevent>
    <div class="row">
      <div class="col col-6">
        <FormInput
          v-model="values.table_id"
          type="number"
          small-label
          :label="$t('localBaserowListRowsForm.tableFieldLabel')"
          :placeholder="$t('localBaserowListRowsForm.tableFieldPlaceHolder')"
          :from-value="(value) => (value ? value : '')"
          :to-value="(value) => (value ? value : null)"
        />
      </div>
      <div class="col col-6">
        <FormInput
          v-model="values.view_id"
          type="number"
          small-label
          :label="$t('localBaserowListRowsForm.viewFieldLabel')"
          :placeholder="$t('localBaserowListRowsForm.viewFieldPlaceHolder')"
          :from-value="(value) => (value ? value : '')"
          :to-value="(value) => (value ? value : null)"
        />
      </div>
    </div>
    <div class="row">
      <div class="col col-12">
        <Tabs>
          <Tab :title="$t('localBaserowListRowsForm.searchTabTitle')">
            <FormInput
              v-model="values.search_query"
              type="text"
              small-label
              :placeholder="
                $t('localBaserowListRowsForm.searchFieldPlaceHolder')
              "
            />
          </Tab>
        </Tabs>
      </div>
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'

export default {
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      allowedValues: ['table_id', 'view_id', 'search_query'],
      values: {
        table_id: null,
        view_id: null,
        search_query: '',
      },
    }
  },
}
</script>
