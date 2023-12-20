<template functional>
  <div ref="cell" class="grid-view__cell" :class="data.staticClass || ''">
    <div v-if="props.value" class="field-last-modified-by">
      <div class="field-last-modified-by__name background-color--light-gray">
        <span class="field-last-modified-by__name-text">{{
          $options.methods.getCollaboratorName(props.value, parent.$store)
        }}</span>
      </div>
      <div class="field-last-modified-by__initials">
        {{
          $options.methods.getCollaboratorNameInitials(
            props.value,
            parent.$store
          )
        }}
      </div>
    </div>
  </div>
</template>

<script>
import collaboratorName from '@baserow/modules/database/mixins/collaboratorName'

export default {
  name: 'FunctionalGridViewFieldLastModifiedBy',
  mixins: [collaboratorName],
}
</script>
