<template>
  <MembersTable :group="group" />
</template>

<script>
import MembersTable from '@baserow/modules/core/components/settings/members/MembersTable'

export default {
  name: 'Members',
  components: { MembersTable },
  props: {
    group: {
      type: Object,
      required: true,
    },
  },
}
</script>
