<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormElement class="control">
      <label class="control__label">
        {{ $t('tableElementForm.dataSource') }}
      </label>
      <div class="control__elements">
        <Dropdown v-model="values.data_source_id" :show-search="false">
          <DropdownItem
            v-for="dataSource in availableDataSources"
            :key="dataSource.id"
            :name="dataSource.name"
            :value="dataSource.id"
          />
        </Dropdown>
      </div>
    </FormElement>
    <FormInput
      v-model="values.items_per_page"
      :label="$t('tableElementForm.itemsPerPage')"
      :placeholder="$t('tableElementForm.itemsPerPagePlaceholder')"
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
    <FormElement class="control">
      <label class="control__label">
        {{ $t('tableElementForm.fields') }}
      </label>
      <template v-if="values.data_source_id">
        <div>
          <Expandable
            v-for="(field, index) in values.fields"
            :key="field.id"
            v-sortable="{
              id: field.id,
              update: orderFields,
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
                  class="fas"
                  :class="
                    expanded
                      ? 'iconoir-nav-arrow-down'
                      : 'iconoir-nav-arrow-right'
                  "
                />
              </div>
            </template>
            <template #default>
              <FormInput
                v-model="field.name"
                class="table-element-form__field-label"
                label="Name"
                horizontal
                :error="
                  !$v.values.fields.$each[index].name.required
                    ? $t('error.requiredField')
                    : !$v.values.fields.$each[index].name.maxLength
                    ? $t('error.maxLength', { max: 255 })
                    : ''
                "
              >
                <template v-if="values.fields.length > 1" #after-input>
                  <Button
                    icon="iconoir-bin"
                    type="light"
                    @click="removeField(field)"
                  />
                </template>
              </FormInput>
              <FormElement class="control control--horizontal">
                <label class="control__label">
                  {{ $t('tableElementForm.fieldType') }}
                </label>
                <div class="control__elements">
                  <Dropdown
                    :value="field.type"
                    :show-search="false"
                    @input="changeFieldType(field, $event)"
                  >
                    <DropdownItem
                      v-for="collectionType in orderedCollectionTypes"
                      :key="collectionType.getType()"
                      :name="collectionType.name"
                      :value="collectionType.getType()"
                    />
                  </Dropdown>
                </div>
              </FormElement>
              <component
                :is="collectionTypes[field.type].formComponent"
                :element="element"
                :default-values="field"
                @values-changed="updateField(field, $event)"
              />
            </template>
          </Expandable>
        </div>
        <Button
          prepend-icon="baserow-icon-plus"
          type="link"
          size="tiny"
          @click="addField"
        >
          {{ $t('tableElementForm.addField') }}
        </Button>
      </template>
      <p v-else>{{ $t('tableElementForm.selectSourceFirst') }}</p>
    </FormElement>
    <ColorInputGroup
      v-model="values.button_color"
      :label="$t('tableElementForm.buttonColor')"
      :color-variables="colorVariables"
    />
  </form>
</template>

<script>
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'
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
import { mapGetters } from 'vuex'
import elementForm from '@baserow/modules/builder/mixins/elementForm'

export default {
  name: 'TableElementForm',
  components: { ApplicationBuilderFormulaInputGroup },
  mixins: [elementForm],
  data() {
    return {
      allowedValues: ['data_source_id', 'fields', 'items_per_page'],
      values: {
        data_source_id: null,
        items_per_page: 1,
        fields: [],
      },
    }
  },
  computed: {
    dataSources() {
      return this.$store.getters['dataSource/getPageDataSources'](this.page)
    },
    availableDataSources() {
      return this.dataSources.filter(
        (dataSource) =>
          dataSource.type &&
          this.$registry.get('service', dataSource.type).returnsList
      )
    },
    selectedDataSource() {
      if (!this.values.data_source_id) {
        return null
      }
      return this.$store.getters['dataSource/getPageDataSourceById'](
        this.page,
        this.values.data_source_id
      )
    },
    selectedDataSourceType() {
      if (!this.selectedDataSource || !this.selectedDataSource.type) {
        return null
      }
      return this.$registry.get('service', this.selectedDataSource.type)
    },
    maxItemPerPage() {
      if (!this.selectedDataSourceType) {
        return 20
      }
      return this.selectedDataSourceType.maxResultLimit
    },
    orderedCollectionTypes() {
      return this.$registry.getOrderedList('collectionField')
    },
    collectionTypes() {
      return this.$registry.getAll('collectionField')
    },
    ...mapGetters({
      element: 'element/getSelected',
    }),
  },
  watch: {
    'dataSources.length'(newValue, oldValue) {
      if (this.values.data_source_id && oldValue > newValue) {
        if (
          !this.dataSources.some(({ id }) => id === this.values.data_source_id)
        ) {
          // Remove the data_source_id if the related dataSource has been deleted.
          this.values.data_source_id = null
        }
      }
    },
  },
  methods: {
    addField() {
      this.values.fields.push({
        name: getNextAvailableNameInSequence(
          this.$t('tableElementForm.fieldDefaultName'),
          this.values.fields.map(({ name }) => name)
        ),
        value: '',
        type: 'text',
        id: uuid(), // Temporary id
      })
    },
    changeFieldType(fieldToUpdate, newType) {
      this.values.fields = this.values.fields.map((field) => {
        if (field.id === fieldToUpdate.id) {
          return { id: field.id, name: field.name, type: newType }
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
