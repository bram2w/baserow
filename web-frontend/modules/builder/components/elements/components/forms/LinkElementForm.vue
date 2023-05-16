<template>
  <form @submit.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.text') }}
      </label>
      <div class="control__elements">
        <input
          v-model="values.value"
          type="text"
          class="input"
          :placeholder="$t('linkElementForm.textPlaceholder')"
        />
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.navigateTo') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="navigateTo" :show-search="false">
          <template #value>
            <template v-if="destinationPage">
              {{ destinationPage.name }}
              <span class="link-element-form__navigate-option-page-path">
                {{ destinationPage.path }}
              </span></template
            >
            <span v-else>{{ $t('linkElementForm.navigateToCustom') }}</span>
          </template>
          <DropdownItem
            v-for="page in pages"
            :key="page.id"
            :value="page.id"
            :name="page.name"
          >
            {{ page.name }}
            <span class="link-element-form__navigate-option-page-path">
              {{ page.path }}
            </span>
          </DropdownItem>
          <DropdownItem
            :name="$t('linkElementForm.navigateToCustom')"
            value="custom"
          ></DropdownItem>
        </Dropdown>
      </div>
    </FormElement>
    <FormElement v-if="navigateTo === 'custom'" class="control">
      <label class="control__label">
        {{ $t('linkElementForm.url') }}
      </label>
      <div class="control__elements">
        <input
          v-model="values.navigate_to_url"
          type="text"
          class="input"
          :placeholder="$t('linkElementForm.urlPlaceholder')"
        />
      </div>
    </FormElement>
    <FormElement
      v-if="destinationPage"
      class="control link-element-form__params"
    >
      <template v-if="parametersInError">
        <Alert type="error" minimal>
          <div class="link-element-form__params-error">
            <div>
              {{ $t('linkElementForm.paramsInErrorDescription') }}
            </div>
            <Button
              color="error"
              size="tiny"
              @click.prevent="updatePageParameters"
            >
              {{ $t('linkElementForm.paramsInErrorButton') }}
            </Button>
          </div>
        </Alert>
      </template>
      <div v-else class="control__elements link-element-form__params">
        <template v-for="param in values.page_parameters">
          <!-- eslint-disable-next-line vue/require-v-for-key -->
          <label>{{ param.name }}</label>
          <!-- eslint-disable-next-line vue/require-v-for-key -->
          <input
            v-model="param.value"
            type="text"
            class="input"
            :placeholder="$t('linkElementForm.paramPlaceholder')"
          />
        </template>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.variant') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.variant" value="link">
          {{ $t('linkElementForm.variantLink') }}
        </RadioButton>
        <RadioButton v-model="values.variant" value="button">
          {{ $t('linkElementForm.variantButton') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.alignment') }}
      </label>
      <div class="control__elements">
        <RadioButton
          v-for="alignment in alignments"
          :key="alignment.value"
          v-model="values.alignment"
          :value="alignment.value"
          :icon="alignment.icon"
          :title="alignment.name"
        />
      </div>
    </FormElement>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('linkElementForm.target') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.target" value="self">
          {{ $t('linkElementForm.targetSelf') }}
        </RadioButton>
        <RadioButton v-model="values.target" value="blank">
          {{ $t('linkElementForm.targetNewTab') }}
        </RadioButton>
      </div>
    </FormElement>
    <FormElement v-if="values.variant === 'button'" class="control">
      <label class="control__label">
        {{ $t('linkElementForm.width') }}
      </label>
      <div class="control__elements">
        <RadioButton v-model="values.width" value="auto">
          {{ $t('linkElementForm.widthAuto') }}
        </RadioButton>
        <RadioButton v-model="values.width" value="full">
          {{ $t('linkElementForm.widthFull') }}
        </RadioButton>
      </div>
    </FormElement>
  </form>
</template>

<script>
import form from '@baserow/modules/core/mixins/form'
import { LinkElementType } from '@baserow/modules/builder/elementTypes'

export default {
  name: 'LinkElementForm',
  mixins: [form],
  props: { builder: { type: Object, required: true } },
  data() {
    let navigateTo = ''
    if (this.defaultValues.navigation_type === 'page') {
      if (this.defaultValues.navigate_to_page_id) {
        navigateTo = this.defaultValues.navigate_to_page_id
      }
    } else {
      navigateTo = 'custom'
    }
    return {
      values: {
        value: '',
        alignment: 'left',
        variant: 'link',
        navigation_type: 'page',
        navigate_to_page_id: null,
        navigate_to_url: '',
        page_parameters: [],
        width: 'auto',
        target: 'self',
      },
      parametersInError: false,
      navigateTo,
      alignments: [
        {
          name: this.$t('linkElementForm.alignmentLeft'),
          value: 'left',
          icon: 'align-left',
        },
        {
          name: this.$t('linkElementForm.alignmentCenter'),
          value: 'center',
          icon: 'align-center',
        },
        {
          name: this.$t('linkElementForm.alignmentRight'),
          value: 'right',
          icon: 'align-right',
        },
      ],
    }
  },
  computed: {
    pages() {
      return this.builder.pages
    },
    destinationPage() {
      if (!isNaN(this.navigateTo)) {
        return this.builder.pages.find(({ id }) => id === this.navigateTo)
      }
      return null
    },
  },
  watch: {
    'destinationPage.path_params': {
      handler(value) {
        this.updatePageParameters()
      },
      deep: true,
    },
    navigateTo(value) {
      if (value === '') {
        this.values.navigation_type = 'page'
        this.values.navigate_to_page_id = null
        this.values.navigate_to_url = ''
      } else if (value === 'custom') {
        this.values.navigation_type = 'custom'
      } else if (!isNaN(value)) {
        this.values.navigation_type = 'page'
        this.values.navigate_to_page_id = value
        this.updatePageParameters()
      }
    },
  },
  mounted() {
    if (LinkElementType.arePathParametersInError(this.values, this.builder)) {
      this.parametersInError = true
    }
  },
  methods: {
    updatePageParameters() {
      this.values.page_parameters = (
        this.destinationPage?.path_params || []
      ).map(({ name }, index) => {
        let value = ''
        // Naive way to keep data when we change the destination page.
        if (this.values.page_parameters[index]) {
          value = this.values.page_parameters[index].value
        }
        return { name, value }
      })
      this.parametersInError = false
    },
  },
}
</script>
