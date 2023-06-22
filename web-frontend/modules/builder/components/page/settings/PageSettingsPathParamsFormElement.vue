<template>
  <div>
    <label class="control__label">
      {{ $t('pageForm.pathParamsTitle') }}
    </label>
    <div class="control__description">
      <template v-if="Object.keys(pathParams).length > 0">
        {{ $t('pageForm.pathParamsSubtitle') }}
      </template>
      <template v-else>
        {{ $t('pageForm.pathParamsSubtitleTutorial') }}
      </template>
    </div>
    <div
      v-for="pathParam in pathParams"
      :key="pathParam.name"
      class="page-settings-path-params"
    >
      <span class="page-settings-path-params__name">{{ pathParam.name }}</span>
      <div class="page-settings-path-params__dropdown">
        <Dropdown
          :value="pathParam.type"
          @input="$emit('update', pathParam.name, $event)"
        >
          <DropdownItem
            v-for="pathParamType in pathParamTypes"
            :key="pathParamType.getType()"
            :name="pathParamType.name"
            :value="pathParamType.getType()"
          ></DropdownItem>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PageSettingsPathParamsFormElement',
  props: {
    pathParams: {
      type: Array,
      required: false,
      default: () => {},
    },
  },
  computed: {
    pathParamTypes() {
      return this.$registry.getOrderedList('pathParamType')
    },
  },
}
</script>
