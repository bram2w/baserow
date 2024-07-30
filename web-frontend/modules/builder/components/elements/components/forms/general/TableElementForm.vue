<template>
  <form class="table-element-form" @submit.prevent @keydown.enter.prevent>
    <CustomStyle
      v-model="values.styles"
      style-key="table"
      :config-block-types="['table', 'typography']"
      :theme="builder.theme"
      :extra-args="{ onlyBody: true, noAlignment: true }"
    />
    <FormGroup
      class="margin-bottom-2"
      small-label
      required
      :label="$t('tableElementForm.dataSource')"
    >
      <div @click="userHasChangedDataSource = true">
        <Dropdown v-model="values.data_source_id" :show-search="false" small>
          <DropdownItem
            v-for="dataSource in availableDataSources"
            :key="dataSource.id"
            :name="dataSource.name"
            :value="dataSource.id"
          />
        </Dropdown>
      </div>
    </FormGroup>

    <FormGroup
      class="margin-bottom-2"
      small-label
      :label="$t('tableElementForm.itemsPerPage')"
      required
      :error-message="errorMessageItemsPerPage"
    >
      <FormInput
        v-model="values.items_per_page"
        :placeholder="$t('tableElementForm.itemsPerPagePlaceholder')"
        :to-value="(value) => parseInt(value)"
        type="number"
        @blur="$v.values.items_per_page.$touch()"
      />
    </FormGroup>

    <CustomStyle
      v-model="values.styles"
      style-key="button"
      :config-block-types="['button']"
      :theme="builder.theme"
    />
    <FormGroup
      small-label
      :label="$t('tableElementForm.buttonLoadMoreLabel')"
      class="margin-bottom-2"
      required
    >
      <InjectedFormulaInput
        v-model="values.button_load_more_label"
        :placeholder="$t('elementForms.textInputPlaceholder')"
      />
    </FormGroup>

    <FormSection class="margin-bottom-2" :title="$t('tableElementForm.fields')">
      <template v-if="values.data_source_id">
        <ButtonText
          type="primary"
          icon="iconoir-refresh-double"
          size="small"
          class="table-element-form__refresh-fields-button"
          @click="refreshFieldsFromDataSource"
        >
          {{ $t('tableElementForm.refreshFieldsFromDataSource') }}
        </ButtonText>
        <div>
          <Expandable
            v-for="(field, index) in values.fields"
            :key="field.id"
            v-sortable="{
              id: field.id,
              update: orderFields,
              enabled: $hasPermission(
                'builder.page.element.update',
                element,
                workspace.id
              ),
              handle: '[data-sortable-handle]',
            }"
            class="table-element-form__field"
          >
            <template #header="{ toggle, expanded }">
              <div
                class="table-element-form__field-header"
                @click.stop="toggle"
              >
                <div
                  class="table-element-form__field-handle"
                  data-sortable-handle
                />
                <div class="table-element-form__field-name">
                  <i
                    v-if="!expanded && fieldInError(field)"
                    class="table-element-form__field-error iconoir-warning-circle"
                  ></i>
                  {{ field.name }}
                </div>
                <i
                  :class="
                    expanded
                      ? 'iconoir-nav-arrow-down'
                      : 'iconoir-nav-arrow-right'
                  "
                />
              </div>
            </template>
            <template #default>
              <FormGroup
                small-label
                horizontal
                required
                class="margin-bottom-2"
                :label="$t('tableElementForm.name')"
                :error-message="
                  !$v.values.fields.$each[index].name.required
                    ? $t('error.requiredField')
                    : !$v.values.fields.$each[index].name.maxLength
                    ? $t('error.maxLength', { max: 255 })
                    : ''
                "
              >
                <FormInput
                  v-model="field.name"
                  class="table-element-form__field-label"
                >
                </FormInput>
                <template v-if="values.fields.length > 1" #after-input>
                  <ButtonIcon icon="iconoir-bin" @click="removeField(field)" />
                </template>
              </FormGroup>

              <FormGroup
                small-label
                horizontal
                required
                :label="$t('tableElementForm.fieldType')"
                class="margin-bottom-2"
              >
                <Dropdown
                  :value="field.type"
                  :show-search="false"
                  small
                  @input="changeFieldType(field, $event)"
                >
                  <DropdownItem
                    v-for="collectionType in orderedCollectionTypes"
                    :key="collectionType.getType()"
                    :name="collectionType.name"
                    :value="collectionType.getType()"
                  />
                </Dropdown>
              </FormGroup>
              <component
                :is="collectionTypes[field.type].formComponent"
                :element="element"
                :default-values="field"
                :base-theme="collectionFieldBaseTheme"
                :application-context-additions="{
                  collectionField: field,
                }"
                @values-changed="updateField(field, $event)"
              />
            </template>
          </Expandable>
        </div>
        <ButtonText
          type="primary"
          icon="iconoir-plus"
          size="small"
          @click="addField"
        >
          {{ $t('tableElementForm.addField') }}
        </ButtonText>
      </template>
      <p v-else>{{ $t('tableElementForm.selectSourceFirst') }}</p>
    </FormSection>
    <FormGroup :label="$t('tableElementForm.orientation')" small-label required>
      <DeviceSelector
        :device-type-selected="deviceTypeSelected"
        direction="row"
        @selected="actionSetDeviceTypeSelected"
      >
        <template #deviceTypeControl="{ deviceType }">
          <RadioButton
            v-model="values.orientation[deviceType.getType()]"
            icon="iconoir-view-columns-3"
            :value="TABLE_ORIENTATION.HORIZONTAL"
          >
            {{ $t('tableElementForm.orientationHorizontal') }}
          </RadioButton>
          <RadioButton
            v-model="values.orientation[deviceType.getType()]"
            icon="iconoir-table-rows"
            :value="TABLE_ORIENTATION.VERTICAL"
          >
            {{ $t('tableElementForm.orientationVertical') }}
          </RadioButton>
        </template>
      </DeviceSelector>
    </FormGroup>
  </form>
</template>

<script>
import InjectedFormulaInput from '@baserow/modules/core/components/formula/InjectedFormulaInput'
import {
  getNextAvailableNameInSequence,
  uuid,
} from '@baserow/modules/core/utils/string'
import {
  required,
  maxLength,
  integer,
  minValue,
  maxValue,
} from 'vuelidate/lib/validators'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import collectionElementForm from '@baserow/modules/builder/mixins/collectionElementForm'
import { TABLE_ORIENTATION } from '@baserow/modules/builder/enums'
import DeviceSelector from '@baserow/modules/builder/components/page/header/DeviceSelector.vue'
import { mapActions, mapGetters } from 'vuex'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'

export default {
  name: 'TableElementForm',
  components: {
    InjectedFormulaInput,
    DeviceSelector,
    CustomStyle,
  },
  mixins: [elementForm, collectionElementForm],
  data() {
    return {
      allowedValues: [
        'data_source_id',
        'fields',
        'items_per_page',
        'orientation',
        'styles',
        'button_load_more_label',
      ],
      values: {
        fields: [],
        data_source_id: null,
        items_per_page: 1,
        styles: {},
        orientation: {},
        button_load_more_label: '',
      },
      userHasChangedDataSource: false,
    }
  },
  computed: {
    ...mapGetters({ deviceTypeSelected: 'page/getDeviceTypeSelected' }),
    TABLE_ORIENTATION() {
      return TABLE_ORIENTATION
    },
    orderedCollectionTypes() {
      return this.$registry.getOrderedList('collectionField')
    },
    collectionTypes() {
      return this.$registry.getAll('collectionField')
    },
    collectionFieldBaseTheme() {
      return { ...this.builder.theme, ...this.values.styles?.table }
    },
    errorMessageItemsPerPage() {
      return this.$v.values.items_per_page.$dirty &&
        !this.$v.values.items_per_page.required
        ? this.$t('error.requiredField')
        : !this.$v.values.items_per_page.integer
        ? this.$t('error.integerField')
        : !this.$v.values.items_per_page.minValue
        ? this.$t('error.minValueField', { min: 1 })
        : !this.$v.values.items_per_page.maxValue
        ? this.$t('error.maxValueField', { max: this.maxItemPerPage })
        : ''
    },
  },
  watch: {
    async 'values.data_source_id'(newValue, oldValue) {
      if (newValue && !oldValue) {
        await this.$nextTick()
        if (this.userHasChangedDataSource) {
          this.refreshFieldsFromDataSource()
        }
      }
    },
  },
  methods: {
    ...mapActions({
      actionSetDeviceTypeSelected: 'page/setDeviceTypeSelected',
    }),
    addField() {
      this.values.fields.push({
        name: getNextAvailableNameInSequence(
          this.$t('tableElementForm.fieldDefaultName'),
          this.values.fields.map(({ name }) => name)
        ),
        value: '',
        type: 'text',
        id: uuid(), // Temporary id
        uid: uuid(),
      })
    },
    changeFieldType(fieldToUpdate, newType) {
      this.values.fields = this.values.fields.map((field) => {
        if (field.id === fieldToUpdate.id) {
          // When the type of the workflow action changes we assign a new UID to
          // trigger the backend workflow action removal
          return {
            id: field.id,
            uid: uuid(),
            name: field.name,
            type: newType,
          }
        }
        return field
      })
    },
    updateField(fieldToUpdate, values) {
      this.values.fields = this.values.fields.map((field) => {
        if (field.id === fieldToUpdate.id) {
          return { ...field, ...values }
        }
        return field
      })
    },
    removeField(field) {
      this.values.fields = this.values.fields.filter((item) => item !== field)
    },
    orderFields(newOrder) {
      const fieldById = Object.fromEntries(
        this.values.fields.map((field) => [field.id, field])
      )
      this.values.fields = newOrder.map((fieldId) => fieldById[fieldId])
    },
    fieldInError(field) {
      return this.collectionTypes[field.type].isInError({
        field,
        builder: this.builder,
      })
    },
    refreshFieldsFromDataSource() {
      if (this.selectedDataSource?.type) {
        const serviceType = this.$registry.get(
          'service',
          this.selectedDataSource.type
        )
        this.values.fields = serviceType.getDefaultCollectionFields(
          this.selectedDataSource
        )
      }
    },
  },
  validations() {
    return {
      values: {
        fields: {
          $each: {
            name: {
              required,
              maxLength: maxLength(225),
            },
          },
        },
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
