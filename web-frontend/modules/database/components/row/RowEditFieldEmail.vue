<template>
  <div class="control__elements">
    <input
      ref="input"
      v-model="copy"
      type="text"
      class="input input--large"
      :class="{ 'input--error': !isValid() }"
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
import EmailField from '@baserow/modules/database/mixins/EmailField'

export default {
  mixins: [rowEditField, rowEditFieldInput, EmailField],
}
</script>
