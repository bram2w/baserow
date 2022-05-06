<template>
  <div class="filters__value-timezone">{{ filter.value }}</div>
</template>

<script>
import viewFilter from '@baserow/modules/database/mixins/viewFilter'

export default {
  name: 'ViewFilterTypeTimeZone',
  mixins: [viewFilter],
}
</script>
