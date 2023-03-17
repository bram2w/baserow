<template>
  <header class="layout__col-2-1 header header--space-between">
    <ul class="header__filter">
      <li class="header__filter-item">
        <PageHeaderElements />
      </li>
    </ul>
    <DeviceSelector
      :device-type-selected="deviceTypeSelected"
      @selected="actionSetDeviceTypeSelected"
    />
  </header>
</template>

<script>
import PageHeaderElements from '@baserow/modules/builder/components/elements/PageHeaderElements'
import DeviceSelector from '@baserow/modules/builder/components/page/DeviceSelector'
import { mapActions, mapGetters } from 'vuex'
export default {
  name: 'PageHeader',
  components: { DeviceSelector, PageHeaderElements },
  computed: {
    ...mapGetters({ deviceTypeSelected: 'page/getDeviceTypeSelected' }),
    deviceTypes() {
      return Object.values(this.$registry.getOrderedList('device'))
    },
  },
  created() {
    if (this.deviceTypeSelected === null) {
      this.$store.dispatch(
        'page/setDeviceTypeSelected',
        this.deviceTypes[0].getType()
      )
    }
  },
  methods: {
    ...mapActions({
      actionSetDeviceTypeSelected: 'page/setDeviceTypeSelected',
    }),
  },
}
</script>
