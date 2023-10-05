<template>
  <form @submit.prevent>
    <LocalBaserowTableSelector
      v-model="values.table_id"
      :databases="databases"
      :view-id.sync="values.view_id"
    ></LocalBaserowTableSelector>
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
import LocalBaserowTableSelector from '@baserow/modules/integrations/components/services/LocalBaserowTableSelector'

export default {
  components: { LocalBaserowTableSelector },
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    contextData: {
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
  computed: {
    databases() {
      return this.contextData?.databases || []
    },
  },
}
</script>
