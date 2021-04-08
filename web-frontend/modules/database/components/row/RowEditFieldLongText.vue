<template>
  <div class="control__elements">
    <textarea
      ref="input"
      v-model="copy"
      type="text"
      class="input input--large field-long-text"
      :disabled="readOnly"
      @focus="select()"
      @blur="unselect()"
    />
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'

export default {
  mixins: [rowEditField, rowEditFieldInput],
}
</script>
