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
    <FormGroup :label="$t('repeatElementForm.orientationLabel')">
      <RadioButton
        v-model="values.orientation"
        value="vertical"
        icon="iconoir-table-rows"
      >
        {{ $t('repeatElementForm.orientationVertical') }}
      </RadioButton>
      <RadioButton
        v-model="values.orientation"
        value="horizontal"
        icon="iconoir-view-columns-3"
      >
        {{ $t('repeatElementForm.orientationHorizontal') }}
      </RadioButton>
    </FormGroup>
    <FormGroup
      v-if="values.orientation === 'horizontal'"
      :error="getItemsPerRowError"
      :label="$t('repeatElementForm.itemsPerRowLabel')"
      :description="$t('repeatElementForm.itemsPerRowDescription')"
    >
      <DeviceSelector
        :device-type-selected="deviceTypeSelected"
        class="repeat-element__device-selector"
        @selected="actionSetDeviceTypeSelected"
      >
        <template #deviceTypeControl="{ deviceType }">
          <input
            :ref="`itemsPerRow-${deviceType.getType()}`"
            v-model="values.items_per_row[deviceType.getType()]"
            :class="{
              'input--error':
                $v.values.items_per_row[deviceType.getType()].$error,
              'remove-number-input-controls': true,
            }"
            type="number"
            class="input"
            @input="handlePerRowInput($event, deviceType.getType())"
          />
        </template>
      </DeviceSelector>
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

export default {
  name: 'RepeatElementForm',
  components: { DeviceSelector },
  mixins: [elementForm, collectionElementForm],
  data() {
    return {
      allowedValues: [
        'data_source_id',
        'items_per_page',
        'items_per_row',
        'orientation',
      ],
      values: {
        data_source_id: null,
        items_per_page: 1,
        items_per_row: {},
        orientation: 'vertical',
      },
    }
  },
  computed: {
    ...mapGetters({ deviceTypeSelected: 'page/getDeviceTypeSelected' }),
    deviceTypes() {
      return Object.values(this.$registry.getOrderedList('device'))
    },
    getItemsPerRowError() {
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
    handlePerRowInput(event, deviceTypeType) {
      this.$v.values.items_per_row[deviceTypeType].$touch()
      this.values.items_per_row[deviceTypeType] = parseInt(event.target.value)
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
