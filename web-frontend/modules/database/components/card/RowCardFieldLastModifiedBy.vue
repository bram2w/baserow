<template functional>
  <div class="field-last-modified-by field-last-modified-by--card">
    <div
      v-if="props.value"
      class="field-last-modified-by__name background-color--light-gray"
    >
      <span class="field-last-modified-by__name-text">{{
        $options.methods.getCollaboratorName(props.value, parent.$store)
      }}</span>
    </div>
    <div v-if="props.value" class="field-last-modified-by__initials">
      {{
        $options.methods.getCollaboratorNameInitials(props.value, parent.$store)
      }}
    </div>
  </div>
</template>

<script>
import collaboratorName from '@baserow/modules/database/mixins/collaboratorName'

export default {
  height: 30,
  mixins: [collaboratorName],
}
</script>
