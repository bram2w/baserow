<template>
  <form @submit.prevent @keydown.enter.prevent>
    <CustomStyleButton
      v-model="values.styles"
      style-key="input"
      :config-block-types="['input']"
      :theme="builder.theme"
    />
    <FormGroup
      small-label
      :label="$t('generalForm.labelTitle')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.label"
        :placeholder="$t('generalForm.labelPlaceholder')"
      />
    </FormGroup>
    <ValueFormatSelector
      v-model="values.label"
      :label="$t('textFormatSelector.labelFormat')"
    />
    <FormGroup
      small-label
      :label="$t('generalForm.valueTitle')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.default_value"
        :placeholder="$t('generalForm.valuePlaceholder')"
      />
    </FormGroup>
    <FormGroup
      small-label
      :label="$t('generalForm.placeholderTitle')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.placeholder"
        :placeholder="$t('generalForm.placeholderPlaceholder')"
      />
    </FormGroup>
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
      <RadioGroup
        v-model="values.option_type"
        :options="optionTypeOptions"
        type="button"
      />
    </FormGroup>
    <TextFormatSelector
      v-model="optionFormat"
      :label="$t('choiceElementForm.optionFormat')"
    />
    <template v-if="values.option_type === CHOICE_OPTION_TYPES.MANUAL">
      <template v-if="values.options.length">
        <div class="row" style="--gap: 6px">
          <label class="col col-5 control__label control__label--small">
            {{ $t('choiceOptionSelector.name') }}
          </label>
          <label class="col col-7 control__label control__label--small">
            {{ $t('choiceOptionSelector.value') }}
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
              :model-value="optionName(option)"
              :placeholder="$t('choiceOptionSelector.namePlaceholder')"
              @update:model-value="setOptionName(option, $event)"
            />
          </div>
          <div class="col col-5">
            <FormInput
              :value="option.value === null ? optionName(option) : option.value"
              :placeholder="$t('choiceOptionSelector.valuePlaceholder')"
              :class="{
                'choice-element__option-value--fake': option.value === null,
              }"
              @input="option.value = $event"
            />
          </div>
          <div class="col col-2">
            <ButtonIcon icon="iconoir-bin" @click="deleteOption(option)" />
          </div>
        </div>
      </template>
      <template v-else>
        <div class="row" style="--gap: 6px">
          <label class="col control__label control__label--small">
            {{ $t('choiceOptionSelector.addOptionDescription') }}
          </label>
        </div>
      </template>
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
      <FormGroup
        small-label
        :label="$t('choiceOptionSelector.name')"
        class="margin-bottom-2"
      >
        <InjectedFormulaInput
          v-model="values.formula_name"
          :placeholder="$t('choiceOptionSelector.namePlaceholder')"
        />
      </FormGroup>
      <FormGroup
        small-label
        :label="$t('choiceOptionSelector.value')"
        class="margin-bottom-2"
        required
      >
        <InjectedFormulaInput
          v-model="values.formula_value"
          :placeholder="$t('choiceOptionSelector.valuePlaceholder')"
        />
      </FormGroup>
    </template>
  </form>
</template>

<script>
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput.vue'
import {
  CHOICE_OPTION_TYPES,
  TEXT_FORMAT_TYPES,
} from '@baserow/modules/builder/enums'
import CustomStyleButton from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyleButton'
import formElementForm from '@baserow/modules/builder/mixins/formElementForm'
import { uuid } from '@baserow/modules/core/utils/string'
import {
  addPrefix,
  getFormat,
  getFormulaFormat,
  setFormat,
  setFormulaFormat,
  stripFormat,
} from '@baserow/modules/core/formula/textFormat'
import TextFormatSelector from '@baserow/modules/builder/components/elements/components/forms/TextFormatSelector'
import ValueFormatSelector from '@baserow/modules/builder/components/elements/components/forms/ValueFormatSelector'

export default {
  name: 'ChoiceElementForm',
  components: {
    InjectedFormulaInput,
    CustomStyleButton,
    TextFormatSelector,
    ValueFormatSelector,
  },
  mixins: [formElementForm],
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
        label: {},
        default_value: {},
        required: false,
        placeholder: {},
        options: [],
        multiple: false,
        show_as_dropdown: true,
        option_type: CHOICE_OPTION_TYPES.MANUAL,
        formula_name: {},
        formula_value: {},
        styles: {},
      },
      /**
       * The option names carry their own text format marker (see
       * `core/formula/textFormat`), so there is no `option_format` property to
       * store: this element-level toggle is initialised from the stored option
       * names and written back into every option name, or into the name formula
       * when the options come from formulas.
       */
      optionFormat: TEXT_FORMAT_TYPES.PLAIN,
    }
  },
  computed: {
    CHOICE_OPTION_TYPES: () => CHOICE_OPTION_TYPES,
    manualOptions() {
      return Array.isArray(this.values.options) ? this.values.options : []
    },
    element() {
      return this.$store.getters['element/getElementById'](
        this.elementPage,
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
    optionTypeOptions() {
      return [
        {
          label: this.$t('choiceOptionSelector.manual'),
          value: CHOICE_OPTION_TYPES.MANUAL,
          icon: 'iconoir-open-select-hand-gesture',
        },
        {
          label: this.$t('choiceOptionSelector.expressions'),
          value: CHOICE_OPTION_TYPES.FORMULAS,
          icon: 'iconoir-sigma-function',
        },
      ]
    },
  },
  watch: {
    'element.options'(options) {
      this.values.options = { ...options }
    },
    optionFormat(format) {
      this.applyOptionFormat(format)
    },
    'values.option_type'() {
      this.applyOptionFormat(this.optionFormat)
    },
  },
  created() {
    this.optionFormat = this.getStoredOptionFormat()
  },
  methods: {
    /**
     * The format the active option type is stored with: the manual options are
     * Markdown when every option name is marked, the formula options when the
     * name formula is.
     */
    getStoredOptionFormat() {
      if (this.values.option_type === CHOICE_OPTION_TYPES.FORMULAS) {
        return getFormulaFormat(this.values.formula_name)
      }
      const options = this.manualOptions
      const allMarkdown =
        options.length > 0 &&
        options.every(
          (option) => getFormat(option.name) === TEXT_FORMAT_TYPES.MARKDOWN
        )
      return allMarkdown ? TEXT_FORMAT_TYPES.MARKDOWN : TEXT_FORMAT_TYPES.PLAIN
    },
    /**
     * Writes the toggle into the stored values of the active option type.
     */
    applyOptionFormat(format) {
      if (this.values.option_type === CHOICE_OPTION_TYPES.FORMULAS) {
        if (getFormulaFormat(this.values.formula_name) !== format) {
          this.values.formula_name = setFormulaFormat(
            this.values.formula_name,
            format
          )
        }
      } else {
        this.manualOptions.forEach((option) => {
          if (getFormat(option.name) !== format) {
            option.name = setFormat(option.name, format)
          }
        })
      }
    },
    optionName(option) {
      return stripFormat(option.name)
    },
    setOptionName(option, name) {
      option.name = addPrefix(name, this.optionFormat)
    },
    createOption() {
      this.values.options.push({
        name: addPrefix('', this.optionFormat),
        value: null,
        id: uuid(),
      })
    },
    deleteOption({ id }) {
      this.values.options = this.values.options.filter(
        (option) => option.id !== id
      )
    },
  },
}
</script>
