<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="input"
      :config-block-types="['input']"
      :theme="builder.theme"
    />
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

    <FormGroup
      :label="$t('choiceOptionSelector.optionType')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioButton
        v-model="values.option_type"
        type="chips"
        :value="CHOICE_OPTION_TYPES.MANUAL"
        icon="iconoir-open-select-hand-gesture"
      >
        {{ $t('choiceOptionSelector.manual') }}
      </RadioButton>
      <RadioButton
        v-model="values.option_type"
        type="chips"
        :value="CHOICE_OPTION_TYPES.FORMULAS"
        icon="iconoir-sigma-function"
      >
        {{ $t('choiceOptionSelector.formulas') }}
      </RadioButton>
    </FormGroup>
    <template v-if="values.option_type === CHOICE_OPTION_TYPES.MANUAL">
      <div class="row" style="--gap: 6px">
        <label class="col col-5 control__label control__label--small">
          {{ $t('choiceOptionSelector.value') }}
        </label>
        <label class="col col-7 control__label control__label--small">
          {{ $t('choiceOptionSelector.name') }}
        </label>
      </div>
      <div
        v-for="option in values.options"
        :key="option.id"
        style="--gap: 6px"
        class="row margin-bottom-1"
      >
        <div class="col col-5">
          <FormInput
            :value="option.value"
            :placeholder="$t('choiceOptionSelector.valuePlaceholder')"
            @input="optionUpdated(option, { value: $event })"
          />
        </div>
        <div class="col col-5">
          <FormInput
            :value="option.name"
            :placeholder="$t('choiceOptionSelector.namePlaceholder')"
            @input="optionUpdated(option, { name: $event })"
          />
        </div>
        <div class="col col-2">
          <ButtonIcon icon="iconoir-bin" @click="deleteOption(option)" />
        </div>
      </div>
      <ButtonText
        type="secondary"
        size="small"
        icon="iconoir-plus"
        :loading="loading"
        @click="createOption"
      >
        {{ $t('choiceOptionSelector.addOption') }}
      </ButtonText>
    </template>
    <template v-else-if="values.option_type === CHOICE_OPTION_TYPES.FORMULAS">
      <ApplicationBuilderFormulaInputGroup
        v-model="values.formula_value"
        class="margin-bottom-2"
        :label="$t('choiceOptionSelector.value')"
        :placeholder="$t('choiceOptionSelector.valuePlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
      />
      <ApplicationBuilderFormulaInputGroup
        v-model="values.formula_name"
        class="margin-bottom-2"
        :label="$t('choiceOptionSelector.name')"
        :placeholder="$t('choiceOptionSelector.namePlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS"
      />
      <!-- temporary fix to show the context menu -->
      <br />
    </template>
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup.vue'
import {
  CHOICE_OPTION_TYPES,
  DATA_PROVIDERS_ALLOWED_FORM_ELEMENTS,
} from '@baserow/modules/builder/enums'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import { uuid } from '@baserow/modules/core/utils/string'

export default {
  name: 'ChoiceElementForm',
  components: {
    ApplicationBuilderFormulaInputGroup,
    CustomStyle,
  },
  mixins: [elementForm],
  props: {
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
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
        'option_type',
        'formula_name',
        'formula_value',
        'styles',
      ],
      values: {
        label: '',
        default_value: '',
        required: false,
        placeholder: '',
        options: [],
        multiple: false,
        show_as_dropdown: true,
        option_type: CHOICE_OPTION_TYPES.MANUAL,
        formula_name: '',
        formula_value: '',
        styles: {},
      },
    }
  },
  computed: {
    CHOICE_OPTION_TYPES: () => CHOICE_OPTION_TYPES,
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
