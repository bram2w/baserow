<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('headingElementForm.levelTitle') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.level" :show-search="false">
          <DropdownItem
            v-for="level in levels"
            :key="level.value"
            :name="level.name"
            :value="level.value"
          >
            {{ level.name }}
          </DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('headingElementForm.textTitle')"
      :placeholder="$t('elementForms.textInputPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { DATA_PROVIDERS_ALLOWED_ELEMENTS } from '@baserow/modules/builder/enums'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'HeaderElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  props: {},
  data() {
    return {
      values: {
        value: '',
        level: 1,
      },
      levels: [...Array(6).keys()].map((level) => ({
        name: this.$t('headingElementForm.headingName', { level: level + 1 }),
        value: level + 1,
      })),
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_ELEMENTS: () => DATA_PROVIDERS_ALLOWED_ELEMENTS,
  },
}
</script>
