<template>
  <Context ref="context">
    <ul class="context__menu">
      <li v-if="canBeEdited(authProvider.type)">
        <a @click="$emit('edit', authProvider.id)">
          <i class="context__menu-icon fas fa-fw fa-pen"></i>
          {{ $t('editAuthProviderMenuContext.edit') }}
        </a>
      </li>
      <li v-if="canBeDeleted(authProvider.type)">
        <a @click="$emit('delete', authProvider.id)">
          <i class="context__menu-icon fas fa-fw fa-trash-alt"></i>
          {{ $t('editAuthProviderMenuContext.delete') }}
        </a>
      </li>
      <slot></slot>
    </ul>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'
import authProviderItemMixin from '@baserow_enterprise/mixins/authProviderItemMixin'

export default {
  name: 'EditAuthProviderMenuContext',
  components: {},
  mixins: [context, authProviderItemMixin],
  props: {
    authProvider: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      deleteLoading: false,
    }
  },
}
</script>
