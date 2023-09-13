<template>
  <form @submit.prevent>
    <FormInput
      v-model="values.view_id"
      type="number"
      small-label
      :label="$t('localBaserowListRowsForm.viewFieldLabel')"
      :placeholder="$t('localBaserowListRowsForm.viewFieldPlaceHolder')"
    />
    <Tabs>
      <Tab :title="$t('localBaserowListRowsForm.searchTabTitle')">
        <FormInput
          v-model="values.search_query"
          type="text"
          small-label
          :placeholder="$t('localBaserowListRowsForm.searchFieldPlaceHolder')"
        />
      </Tab>
    </Tabs>
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
      allowedValues: ['view_id', 'search_query'],
      values: {
        view_id: null,
        search_query: '',
      },
    }
  },
}
</script>
