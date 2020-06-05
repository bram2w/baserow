<template>
  <div class="control-elements">
    <input
      ref="input"
      v-model="copy"
      type="text"
      class="input input-large field-number"
      :class="{ 'input-error': !isValid() }"
      @keyup.enter="$refs.input.blur()"
      @focus="select()"
      @blur="unselect()"
    />
    <div v-show="!isValid()" class="error">
      {{ getError() }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import numberField from '@baserow/modules/database/mixins/numberField'

export default {
  mixins: [rowEditField, rowEditFieldInput, numberField],
}
</script>
