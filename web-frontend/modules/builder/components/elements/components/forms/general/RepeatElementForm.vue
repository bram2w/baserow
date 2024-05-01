<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup :label="$t('repeatElementForm.dataSource')">
      <Dropdown v-model="values.data_source_id" :show-search="false">
        <DropdownItem
          v-for="dataSource in availableDataSources"
          :key="dataSource.id"
          :name="dataSource.name"
          :value="dataSource.id"
        />
      </Dropdown>
    </FormGroup>
    <FormInput
      v-model="values.items_per_page"
      :label="$t('repeatElementForm.itemsPerPage')"
      :placeholder="$t('repeatElementForm.itemsPerPagePlaceholder')"
      :to-value="(value) => parseInt(value)"
      :error="
        $v.values.items_per_page.$dirty && !$v.values.items_per_page.required
          ? $t('error.requiredField')
          : !$v.values.items_per_page.integer
          ? $t('error.integerField')
          : !$v.values.items_per_page.minValue
          ? $t('error.minValueField', { min: 1 })
          : !$v.values.items_per_page.maxValue
          ? $t('error.maxValueField', { max: maxItemPerPage })
          : ''
      "
      type="number"
      @blur="$v.values.items_per_page.$touch()"
    ></FormInput>
  </form>
</template>

<script>
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import collectionElementForm from '@baserow/modules/builder/mixins/collectionElementForm'

export default {
  name: 'RepeatElementForm',
  mixins: [elementForm, collectionElementForm],
  data() {
    return {
      allowedValues: ['data_source_id', 'items_per_page'],
      values: {
        data_source_id: null,
        items_per_page: 1,
      },
    }
  },
  validations() {
    return {
      values: {
        items_per_page: {
          required,
          integer,
          minValue: minValue(1),
          maxValue: maxValue(this.maxItemPerPage),
        },
      },
    }
  },
}
</script>
