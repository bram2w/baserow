<template>
  <Context ref="context">
    <ul class="context__menu">
      <li
        v-for="authProviderType in authProviderTypes"
        :key="authProviderType.type"
      >
        <a @click="$emit('create', authProviderType)">
          <i
            class="context__menu-icon fa-fw"
            :class="getIconClass(authProviderType)"
          ></i>
          {{ getName(authProviderType) }}
        </a>
      </li>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'CreateAuthProviderContext',
  components: {},
  mixins: [context],
  props: {
    authProviderTypes: {
      type: Array,
      required: true,
    },
  },
  methods: {
    getIconClass(providerType) {
      return this.$registry
        .get('authProvider', providerType.type)
        .getIconClass()
    },
    getName(providerType) {
      return this.$registry.get('authProvider', providerType.type).getName()
    },
  },
}
</script>
