<template>
  <form @submit.prevent>
    <div>
      <LocalBaserowTableSelector
        v-model="values.table_id"
        class="local-baserow-get-row-form__table-selector"
        :databases="databases"
        :view-id.sync="values.view_id"
      ></LocalBaserowTableSelector>
      <ApplicationBuilderFormulaInputGroup
        v-model="values.row_id"
        small-label
        :label="$t('localBaserowGetRowForm.rowFieldLabel')"
        :placeholder="$t('localBaserowGetRowForm.rowFieldPlaceHolder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_DATA_SOURCES"
      />
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
    </div>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_DATA_SOURCES } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import LocalBaserowTableSelector from '@baserow/modules/integrations/components/services/LocalBaserowTableSelector'

export default {
  components: {
    LocalBaserowTableSelector,
    ApplicationBuilderFormulaInputGroup,
  },
  mixins: [form],
  props: {
    builder: {
      type: Object,
      required: true,
    },
    contextData: {
      type: Object,
      required: false,
      default: () => ({
        databases: [],
      }),
    },
  },
  data() {
    return {
      allowedValues: ['table_id', 'view_id', 'row_id', 'search_query'],
      values: {
        table_id: null,
        view_id: null,
        row_id: '',
        search_query: '',
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_DATA_SOURCES: () =>
      DATA_PROVIDERS_ALLOWED_DATA_SOURCES,
    databases() {
      return this.contextData?.databases || []
    },
  },
}
</script>
