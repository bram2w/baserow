<template>
  <ul class="header__filter">
    <li
      v-for="(deviceType, index) in deviceTypes"
      :key="deviceType.getType()"
      class="header__filter-item"
      :class="{ 'header__filter-item--no-margin-left': index === 0 }"
    >
      <a
        class="header__filter-link"
        :class="{
          'active active--primary': deviceTypeSelected === deviceType.getType(),
        }"
        @click="$emit('selected', deviceType.getType())"
      >
        <i :class="`header__filter-icon fas fa-${deviceType.iconClass}`"></i>
      </a>
    </li>
  </ul>
</template>

<script>
export default {
  name: 'DeviceSelector',
  props: {
    deviceTypeSelected: {
      type: String,
      required: true,
    },
  },
  computed: {
    deviceTypes() {
      return Object.values(this.$registry.getOrderedList('device'))
    },
  },
}
</script>
