<template>
  <form @submit.prevent @keydown.enter.prevent>
    <Radio v-model="selectedVisibility" :value="visibilityAll">
      {{ $t('visibilityForm.allVisitors') }}
    </Radio>
    <Expandable :force-expanded="selectedVisibility === visibilityLoggedIn">
      <template #header="{ toggle }">
        <Radio
          v-model="selectedVisibility"
          :value="visibilityLoggedIn"
          @click="toggle"
        >
          {{ $t('visibilityForm.loggedInVisitors') }}
        </Radio>
      </template>

      <template #default>
        <FormElement class="control visibility-form__expanded-form-element">
          <Dropdown
            v-model="selectedRoleType"
            :placeholder="$t('visibilityForm.roleTypesHint')"
            small
          >
            <DropdownItem
              v-for="(value, key) in roleTypeOptions"
              :key="key"
              :name="value"
              :value="key"
            >
            </DropdownItem>
          </Dropdown>

          <div
            v-if="allowAllRolesExceptSelected || disallowAllRolesExceptSelected"
            class="visibility-form__role-checkbox-container"
          >
            <template v-if="loadingRoles">
              <div class="loading margin-bottom-1"></div>
            </template>
            <template v-else>
              <div
                v-for="roleName in allRoles"
                :key="roleName"
                class="visibility-form__role-checkbox-div"
              >
                <Checkbox
                  :checked="isChecked(roleName)"
                  @input="checkRole(roleName)"
                >
                  {{ getRoleName(roleName) }}
                </Checkbox>
              </div>

              <div class="visibility-form__role-links">
                <a @click.prevent="selectAllRoles">
                  {{ $t('visibilityForm.rolesSelectAll') }}
                </a>
                <a
                  class="visibility-form__role-links-deselect-all"
                  @click.prevent="deselectAllRoles"
                >
                  {{ $t('visibilityForm.rolesDeselectAll') }}
                </a>
              </div>
            </template>
          </div>
        </FormElement>
      </template>
    </Expandable>
    <Radio v-model="selectedVisibility" :value="visibilityNotLogged">
      {{ $t('visibilityForm.notLoggedInVisitors') }}
    </Radio>
    <Alert type="warning">
      <slot name="title">{{ $t('visibilityForm.warningTitle') }}</slot>
      <!-- eslint-disable-next-line vue/no-v-html vue/no-v-text-v-html-on-component -->
      <p v-html="$t('visibilityForm.warningMessage')"></p>
    </Alert>
  </form>
</template>

<script>
import { mapGetters } from 'vuex'
import elementForm from '@baserow/modules/builder/mixins/elementForm'
import UserSourceService from '@baserow/modules/core/services/userSource'
import {
  DEFAULT_USER_ROLE_PREFIX,
  VISIBILITY_ALL,
  VISIBILITY_NOT_LOGGED,
  VISIBILITY_LOGGED_IN,
  ROLE_TYPE_ALLOW_ALL,
  ROLE_TYPE_ALLOW_EXCEPT,
  ROLE_TYPE_DISALLOW_EXCEPT,
} from '@baserow/modules/builder/constants'

export default {
  name: 'VisibilityForm',
  mixins: [elementForm],
  data() {
    return {
      allRoles: [],
      values: {
        visibility: VISIBILITY_ALL,
        roles: [],
        role_type: ROLE_TYPE_ALLOW_ALL,
      },
      visibilityLoggedIn: VISIBILITY_LOGGED_IN,
      visibilityAll: VISIBILITY_ALL,
      visibilityNotLogged: VISIBILITY_NOT_LOGGED,
      loadingRoles: true,
    }
  },
  computed: {
    ...mapGetters({
      elementSelected: 'element/getSelected',
    }),
    allowAllRolesExceptSelected() {
      return this.values.role_type === ROLE_TYPE_ALLOW_EXCEPT
    },
    disallowAllRolesExceptSelected() {
      return this.values.role_type === ROLE_TYPE_DISALLOW_EXCEPT
    },
    roleTypeOptions() {
      return {
        [ROLE_TYPE_ALLOW_ALL]: this.$t('visibilityForm.roleTypeAllowAllRoles'),
        [ROLE_TYPE_DISALLOW_EXCEPT]: this.$t(
          'visibilityForm.roleTypeDisallowAllRolesExcept'
        ),
        [ROLE_TYPE_ALLOW_EXCEPT]: this.$t(
          'visibilityForm.roleTypeAllowAllRolesExcept'
        ),
      }
    },
    userSources() {
      return this.$store.getters['userSource/getUserSources'](this.builder)
    },
    /**
     * When the user changes the role_type, e.g. 'Allow roles...',
     * reset the element's roles.
     */
    selectedRoleType: {
      get() {
        return this.values.role_type
      },
      set(newValue) {
        this.values.role_type = newValue

        if (
          [ROLE_TYPE_ALLOW_EXCEPT, ROLE_TYPE_DISALLOW_EXCEPT].includes(newValue)
        ) {
          this.values.roles = []
        }
      },
    },
    /**
     * When the user changes the visibility, e.g. 'All visitors' radio button,
     * reset the element's roles.
     */
    selectedVisibility: {
      get() {
        return this.values.visibility
      },
      set(newValue) {
        this.values.visibility = newValue
        this.resetElementRoles()
      },
    },
  },
  watch: {
    /**
     * If the userSource changes, we want to ensure the roles for the element
     * are still valid.
     */
    userSources: {
      handler() {
        this.fetchAndSyncUserRoles()
      },
      deep: true,
    },
  },
  async mounted() {
    await this.fetchAndSyncUserRoles()
  },
  methods: {
    checkRole(roleName) {
      if (this.values.roles.includes(roleName)) {
        this.values.roles = this.values.roles.filter(
          (role) => role !== roleName
        )
      } else {
        this.values.roles.push(roleName)
      }
    },

    isChecked(roleName) {
      return this.values.roles.includes(roleName)
    },

    async fetchAndSyncUserRoles() {
      await this.fetchUserRoles()
      this.syncUserRoles()
    },

    /**
     * Fetch all valid user roles.
     */
    async fetchUserRoles() {
      this.loadingRoles = true

      let result
      try {
        result = await UserSourceService(this.$client).fetchUserRoles(
          this.builder.id
        )
      } catch (error) {
        this.$store.dispatch('toast/error', {
          title: this.$t('visibilityForm.errorFetchingRolesTitle'),
          message: this.$t('visibilityForm.errorFetchingRolesMessage'),
        })
        return
      } finally {
        this.loadingRoles = false
      }

      let noRole = false
      let allRoles = Array.from(
        new Set(
          result.data
            .map((userSourceData) => {
              return userSourceData.roles.filter((role) => {
                if (role === '') {
                  noRole = true
                }
                return role !== ''
              })
            })
            .flat()
        )
      ).sort()

      // If noRole exists, prefix to array
      if (noRole) {
        allRoles = ['', ...allRoles]
      }

      this.allRoles = allRoles
    },

    getRoleName(roleName) {
      if (roleName === '') {
        return this.$t('visibilityForm.noRole')
      } else if (roleName.startsWith(DEFAULT_USER_ROLE_PREFIX)) {
        const userSourceId = parseInt(
          roleName.split(DEFAULT_USER_ROLE_PREFIX)[1]
        )
        const userSource = this.$store.getters['userSource/getUserSourceById'](
          this.builder,
          userSourceId
        )
        if (userSource) {
          return this.$t('visibilityForm.rolesAllMembersOf', {
            name: userSource.name,
          })
        }
      }

      return roleName
    },

    /**
     * Ensure that an element's roles never contains any old or otherwise
     * invalid roles. This is done by getting the latest valid roles from the
     * backend and comparing it to the element's roles.
     */
    syncUserRoles() {
      const validRoles = this.allRoles.filter((role) => {
        return this.values.roles.includes(role)
      })

      this.values.roles = validRoles
    },
    resetElementRoles() {
      this.values.roles = []
      this.values.role_type = ROLE_TYPE_ALLOW_ALL
    },

    selectAllRoles() {
      this.values.roles = [...this.allRoles]
    },

    deselectAllRoles() {
      this.values.roles = []
    },
  },
}
</script>
