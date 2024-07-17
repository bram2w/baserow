<template>
  <form @submit.prevent @keydown.enter.prevent>
    <FormGroup
      :label="$t('repeatElementForm.dataSource')"
      small-label
      required
      class="margin-bottom-2"
    >
      <Dropdown v-model="values.data_source_id" :show-search="false" small>
        <DropdownItem
          v-for="dataSource in availableDataSources"
          :key="dataSource.id"
          :name="dataSource.name"
          :value="dataSource.id"
        />
      </Dropdown>
    </FormGroup>

    <FormGroup
      :label="$t('repeatElementForm.itemsPerPage')"
      small-label
      required
      class="margin-bottom-2"
      :error-message="
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
    >
      <FormInput
        v-model="values.items_per_page"
        :placeholder="$t('repeatElementForm.itemsPerPagePlaceholder')"
        :to-value="(value) => parseInt(value)"
        class="margin-bottom-2"
        type="number"
        @blur="$v.values.items_per_page.$touch()"
      ></FormInput>

      <CustomStyle
        v-model="values.styles"
        style-key="button"
        :config-block-types="['button']"
        :theme="builder.theme"
      />
      <ApplicationBuilderFormulaInputGroup
        v-model="values.button_load_more_label"
        :label="$t('repeatElementForm.buttonLoadMoreLabel')"
        :placeholder="$t('elementForms.textInputPlaceholder')"
        :data-providers-allowed="DATA_PROVIDERS_ALLOWED_ELEMENTS"
      />
    </FormGroup>
    <FormGroup
      :label="$t('repeatElementForm.orientationLabel')"
      small-label
      required
      class="margin-bottom-2"
    >
      <RadioGroup
        v-model="values.orientation"
        :options="imageSourceTypeOptions"
        type="button"
      >
      </RadioGroup>
    </FormGroup>
    <FormGroup
      v-if="values.orientation === 'horizontal'"
      :error-message="itemsPerRowError"
      :label="$t('repeatElementForm.itemsPerRowLabel')"
      small-label
      required
      :helper-text="$t('repeatElementForm.itemsPerRowDescription')"
    >
      <DeviceSelector
        :device-type-selected="deviceTypeSelected"
        class="repeat-element__device-selector margin-bottom-2"
        @selected="actionSetDeviceTypeSelected"
      >
        <template #deviceTypeControl="{ deviceType }">
          <FormInput
            :ref="`itemsPerRow-${deviceType.getType()}`"
            v-model="values.items_per_row[deviceType.getType()]"
            remove-number-input-controls
            type="number"
            @input="handlePerRowInput($event, deviceType.getType())"
          />
        </template>
      </DeviceSelector>
    </FormGroup>
    <FormGroup
      small-label
      class="margin-bottom-2"
      :label="$t('repeatElementForm.toggleEditorRepetitionsLabel')"
    >
      <Checkbox :checked="isCollapsed" @input="emitToggleRepetitions($event)">
      </Checkbox>
    </FormGroup>
  </form>
</template>

<script>
import _ from 'lodash'
import { required, integer, minValue, maxValue } from 'vuelidate/lib/validators'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import collectionElementForm from '@baserow/modules/builder/mixins/collectionElementForm'
import DeviceSelector from '@baserow/modules/builder/components/page/header/DeviceSelector.vue'
import { mapActions, mapGetters } from 'vuex'
import CustomStyle from '@baserow/modules/builder/components/elements/components/forms/style/CustomStyle'
import ApplicationBuilderFormulaInputGroup from '@baserow/modules/builder/components/ApplicationBuilderFormulaInputGroup'

export default {
  name: 'RepeatElementForm',
  components: {
    DeviceSelector,
    CustomStyle,
    ApplicationBuilderFormulaInputGroup,
  },
  mixins: [elementForm, collectionElementForm],
  inject: ['applicationContext'],
  data() {
    return {
      allowedValues: [
        'data_source_id',
        'items_per_page',
        'items_per_row',
        'orientation',
        'button_load_more_label',
        'styles',
      ],
      values: {
        data_source_id: null,
        items_per_page: 1,
        items_per_row: {},
        orientation: 'vertical',
        button_load_more_label: '',
        styles: {},
      },
    }
  },
  computed: {
    ...mapGetters({ deviceTypeSelected: 'page/getDeviceTypeSelected' }),
    isCollapsed() {
      const { element } = this.applicationContext
      return this.$store.getters['element/getRepeatElementCollapsed'](element)
    },
    deviceTypes() {
      return Object.values(this.$registry.getOrderedList('device'))
    },
    itemsPerRowError() {
      for (const device of this.deviceTypes) {
        const validation = this.$v.values.items_per_row[device.getType()]
        if (validation.$dirty) {
          if (!validation.integer) {
            return this.$t('error.integerField')
          }
          if (!validation.minValue) {
            return this.$t('error.minValueField', { min: 1 })
          }
          if (!validation.maxValue) {
            return this.$t('error.maxValueField', { max: 10 })
          }
        }
      }
      return ''
    },
    imageSourceTypeOptions() {
      return [
        {
          label: this.$t('repeatElementForm.orientationVertical'),
          value: 'vertical',
          icon: 'iconoir-table-rows',
        },
        {
          label: this.$t('repeatElementForm.orientationHorizontal'),
          value: 'horizontal',
          icon: 'iconoir-view-columns-3',
        },
      ]
    },
  },
  mounted() {
    if (_.isEmpty(this.values.items_per_row)) {
      this.values.items_per_row = this.deviceTypes.reduce((acc, deviceType) => {
        acc[deviceType.getType()] = 2
        return acc
      }, {})
    }
  },
  methods: {
    ...mapActions({
      actionSetDeviceTypeSelected: 'page/setDeviceTypeSelected',
    }),
    emitToggleRepetitions(value) {
      const { element } = this.applicationContext
      this.$store.dispatch('element/setRepeatElementCollapsed', {
        element,
        collapsed: value,
      })
    },
    handlePerRowInput(event, deviceTypeType) {
      this.$v.values.items_per_row[deviceTypeType].$touch()
      this.values.items_per_row[deviceTypeType] = parseInt(event)
      this.$emit('input', this.values)
    },
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
        items_per_row: this.deviceTypes.reduce((acc, deviceType) => {
          acc[deviceType.getType()] = {
            integer,
            minValue: minValue(1),
            maxValue: maxValue(10),
          }
          return acc
        }, {}),
      },
    }
  },
}
</script>
