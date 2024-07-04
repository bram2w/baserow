<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-if="values.level"
      v-model="values.styles"
      style-key="typography"
      :config-block-types="['typography']"
      :theme="builder.theme"
      :extra-args="{ headingLevel: values.level }"
    />
    <FormGroup :label="$t('headingElementForm.levelTitle')">
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
    </FormGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.value"
      :label="$t('headingElementForm.textTitle')"
      :placeholder="$t('elementForms.textInputPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { HORIZONTAL_ALIGNMENTS } from '@baserow/modules/builder/enums'
import CustomStyle from '../style/CustomStyle.vue'

export default {
  name: 'HeaderElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    CustomStyle,
  },
  mixins: [elementForm],
  data() {
    return {
      values: {
        value: '',
        level: 1,
        alignment: HORIZONTAL_ALIGNMENTS.LEFT,
        styles: {},
      },
      levels: [...Array(6).keys()].map((level) => ({
        name: this.$t('headingElementForm.headingName', { level: level + 1 }),
        value: level + 1,
      })),
      allowedValues: ['value', 'level', 'alignment', 'styles'],
    }
  },
}
</script>
