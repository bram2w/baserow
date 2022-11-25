<template>
  <Context>
    <template v-if="Object.keys(subject).length > 0">
      <div class="context__menu-title">
        {{ $t('membersSettings.membersTable.columns.role') }}
      </div>
      <ul class="context__menu context__menu--can-be-active">
        <li v-for="role in roles" :key="role.uid">
          <a
            :class="{ active: subject[roleValueColumn] === role.uid }"
            @click="roleUpdate(role.uid, subject)"
          >
            {{ role.name }}
            <div v-if="role.description" class="context__menu-item-description">
              {{ role.description }}
            </div>
          </a>
        </li>
        <li>
          <a
            v-if="allowRemovingRole"
            class="context__menu-item--delete"
            @click="$emit('delete')"
            >{{ $t('action.remove') }}</a
          >
        </li>
      </ul>
    </template>
  </Context>
</template>

<script>
import context from '@baserow/modules/core/mixins/context'

export default {
  name: 'EditRoleContext',
  mixins: [context],
  props: {
    subject: {
      required: true,
      type: Object,
    },
    roles: {
      required: true,
      type: Array,
    },
    roleValueColumn: {
      type: String,
      required: false,
      default: 'permissions',
    },
    allowRemovingRole: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    roleUpdate(roleNew, subject) {
      if (subject[this.roleValueColumn] === roleNew) {
        return
      }

      this.$emit('update-role', { uid: roleNew, subject })
      this.hide()
    },
  },
}
</script>
