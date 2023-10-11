<template>
  <RowEditFieldFile
    :read-only="true"
    :field="field"
    :value="value"
    :workspace-id="workspaceId"
  >
  </RowEditFieldFile>
</template>

<script>
import baseField from '@baserow/modules/database/mixins/baseField'
import RowEditFieldFile from '@baserow/modules/database/components/row/RowEditFieldFile.vue'

export default {
  components: { RowEditFieldFile },
  mixins: [baseField],
}
</script>
