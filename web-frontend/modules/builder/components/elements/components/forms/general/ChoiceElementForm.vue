<template>
  <form @submit.prevent @keydown.enter.prevent>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.label"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('generalForm.labelTitle')"
      :placeholder="$t('generalForm.labelPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.default_value"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('generalForm.valueTitle')"
      :placeholder="$t('generalForm.valuePlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <ApplicationBuilderFormulaInputGroup
      v-model="values.placeholder"
      class="margin-bottom-2"
      small-label
      required
      :label="$t('generalForm.placeholderTitle')"
      :placeholder="$t('generalForm.placeholderPlaceholder')"
      :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
    ></ApplicationBuilderFormulaInputGroup>
    <FormGroup
      :label="$t('generalForm.requiredTitle')"
      class="margin-bottom-2"
      small-label
      required
    >
      <Checkbox v-model="values.required"></Checkbox>
    </FormGroup>

    <FormGroup
      :label="$t('choiceElementForm.multiple')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Checkbox v-model="values.multiple"></Checkbox>
    </FormGroup>

    <FormGroup
      :label="$t('choiceElementForm.display')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioGroup
        v-model="values.show_as_dropdown"
        :options="displayOptions"
        type="button"
      />
    </FormGroup>

    <ChoiceOptionsSelector
      :options="values.options"
      @update="optionUpdated"
      @create="createOption"
      @delete="deleteOption"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import { DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS } from '@baserow/modules/builder/enums'
import form from '@baserow/modules/core/mixins/form'
import ChoiceOptionsSelector from '@baserow/modules/builder/components/elements/components/forms/general/choice/ChoiceOptionsSelector.vue'
import { uuid } from '@baserow/modules/core/utils/string'

export default {
  name: 'ChoiceElementForm',
  components: { ChoiceOptionsSelector, ApplicationBuilderFormulaInputGroup },
  mixins: [form],
  inject: ['page'],
  data() {
    return {
      allowedValues: [
        'label',
        'default_value',
        'required',
        'placeholder',
        'options',
        'multiple',
        'show_as_dropdown',
      ],
      values: {
        label: '',
        default_value: '',
        required: false,
        placeholder: '',
        options: [],
        multiple: false,
        show_as_dropdown: true,
      },
    }
  },
  computed: {
    DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS: () =>
      DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
    element() {
      return this.$store.getters['element/getElementById'](
        this.page,
        this.values.id
      )
    },
    displayOptions() {
      return [
        {
          title: this.$t('choiceElementForm.dropdown'),
          label: this.$t('choiceElementForm.dropdown'),
          value: true,
          icon: 'iconoir-list',
        },
        {
          title: this.values.multiple
            ? this.$t('choiceElementForm.checkbox')
            : this.$t('choiceElementForm.radio'),
          label: this.values.multiple
            ? this.$t('choiceElementForm.checkbox')
            : this.$t('choiceElementForm.radio'),
          value: false,
          icon: this.values.multiple
            ? 'baserow-icon-check-square'
            : 'iconoir-check-circle',
        },
      ]
    },
  },
  watch: {
    'element.options'(options) {
      this.values.options = options.map((o) => o)
    },
  },
  methods: {
    optionUpdated({ id }, changes) {
      const index = this.values.options.findIndex((option) => option.id === id)
      this.$set(this.values.options, index, {
        ...this.values.options[index],
        ...changes,
      })
    },
    createOption() {
      this.values.options.push({ name: '', value: '', id: uuid() })
    },
    deleteOption({ id }) {
      this.values.options = this.values.options.filter(
        (option) => option.id !== id
      )
    },
  },
}
</script>
