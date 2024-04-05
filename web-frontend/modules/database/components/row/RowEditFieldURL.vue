<template>
  <div class="control__elements">
    <div class="url-input">
      <a
        v-if="!editing"
        :href="getHref(copy)"
        target="_blank"
        rel="nofollow noopener noreferrer"
        class="url-input__link"
        >{{ value }}</a
      >
      <input
        ref="input"
        v-model="copy"
        type="text"
        class="input"
        :class="{
          'input--error': touched && !valid,
          'input--invisible': !editing,
        }"
        :disabled="readOnly"
        @keyup.enter="$refs.input.blur()"
        @focus="select()"
        @blur="unselect()"
      />
    </div>
    <div v-show="touched && !valid" class="error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import rowEditField from '@baserow/modules/database/mixins/rowEditField'
import rowEditFieldInput from '@baserow/modules/database/mixins/rowEditFieldInput'
import { ensureUrlProtocol } from '@baserow/modules/core/utils/url'

export default {
  mixins: [rowEditField, rowEditFieldInput],
  methods: {
    getHref(value) {
      return ensureUrlProtocol(value)
    },
  },
}
</script>
