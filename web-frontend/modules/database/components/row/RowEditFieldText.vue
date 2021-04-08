<template>
  <div class="control__elements">
    <input
      ref="input"
      v-model="copy"
      type="text"
      class="input input--large"
      :disabled="readOnly"
      @keyup.enter="$refs.input.blur()"
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
