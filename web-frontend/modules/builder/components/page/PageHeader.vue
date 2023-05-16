<template>
  <header class="layout__col-2-1 header header--space-between">
    <PageHeaderMenuItems :page="page" />
    <DeviceSelector
      :device-type-selected="deviceTypeSelected"
      @selected="actionSetDeviceTypeSelected"
    />
    <PageActions :page="page" />
  </header>
</template>

<script>
import DeviceSelector from '@baserow/modules/builder/components/page/DeviceSelector'
import PageHeaderMenuItems from '@baserow/modules/builder/components/page/PageHeaderMenuItems'
import PageActions from '@baserow/modules/builder/components/page/PageActions'
import { mapActions, mapGetters } from 'vuex'

export default {
  name: 'PageHeader',
  components: {
    PageHeaderMenuItems,
    DeviceSelector,
    PageActions,
  },
  props: {
    page: {
      type: Object,
      required: true,
    },
  },
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
