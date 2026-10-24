<template>
  <ul class="invite-list__items invite-list__items--scrollable">
    <li class="invite-list__item">
      <div class="invite-list__subject">
        <Avatar :initials="nameAbbreviation(workspace.name)" size="large" />
        <div>
          <div class="invite-list__name">
            {{ $t('shareScope.everyoneAt', { name: workspace.name }) }}
          </div>
          <div class="invite-list__subtitle">
            <template v-for="(entry, index) in roleCounts" :key="entry.uid">
              <span v-if="index > 0"> • </span>
              {{ $t('shareScope.roleCount', entry) }}
            </template>
          </div>
        </div>
      </div>
      <div>
        <a
          ref="fromLink"
          @click="$refs.context.toggle($refs.fromLink, 'bottom', 'right', 4)"
        >
          {{ $t('shareScope.fromWorkspace') }}
          <i class="iconoir-nav-arrow-down"></i>
        </a>
        <Context ref="context" class="scope-inherited-access__context">
          <p class="scope-inherited-access__explanation">
            {{
              $t('shareScope.fromWorkspaceExplanation', {
                type: scopeTypeName,
              })
            }}
          </p>
          <ul class="context__menu">
            <li class="context__menu-item context__menu-item--with-separator">
              <nuxt-link
                class="context__menu-item-link"
                :to="{
                  name: 'settings-members',
                  params: { workspaceId: workspace.id },
                }"
                @click="leave"
              >
                {{ $t('shareScope.manageWorkspaceRoles') }}
              </nuxt-link>
            </li>
          </ul>
        </Context>
      </div>
    </li>
  </ul>
</template>

<script>
import nameAbbreviation from '@baserow/modules/core/filters/nameAbbreviation'

const ROLES_WITHOUT_ACCESS = ['NO_ACCESS', 'NO_ROLE_LOW_PRIORITY']

/**
 * The people who reach the object through their workspace role, summarised per
 * role. Roles on a parent database are not summarised yet. Following the link
 * to the workspace's members page emits `close`, as the dialog has no place on
 * that page.
 */
export default {
  name: 'ScopeInheritedAccess',
  props: {
    workspace: {
      type: Object,
      required: true,
    },
    scopeTypeName: {
      type: String,
      required: true,
    },
  },
  emits: ['close'],
  computed: {
    roleCounts() {
      const counts = {}
      for (const user of this.workspace.users || []) {
        const uid = user.role_uid
        counts[uid] = (counts[uid] || 0) + 1
      }
      return this.workspace._.roles
        .filter(
          (role) =>
            role.isVisible &&
            counts[role.uid] &&
            !ROLES_WITHOUT_ACCESS.includes(role.uid)
        )
        .map((role) => ({
          uid: role.uid,
          role: role.name,
          count: counts[role.uid],
        }))
    },
  },
  methods: {
    nameAbbreviation,
    leave() {
      this.$refs.context.hide()
      this.$emit('close')
    },
  },
}
</script>
