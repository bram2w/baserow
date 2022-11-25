<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="$t('selectMembersList.searchPlaceholder')"
      @keyup="search(activeSearchTerm)"
    />
    <div class="margin-top-2">
      {{
        $t('selectMembersList.selectedAmountLabel', {
          count: usersSelected.length,
        })
      }}
    </div>
    <List
      class="margin-top-2 select-members-list__items"
      :items="usersFiltered"
      :attributes="['email']"
      selectable
      @selected="userSelected"
    >
      <template #left-side="{ item }">
        <div class="select-members-list__user-initials margin-left-1">
          {{ item.name | nameAbbreviation }}
        </div>
        <span
          v-tooltip="item.name"
          class="margin-left-1 select-members-list__user-name"
        >
          {{ item.name }}
        </span>
      </template>
    </List>
    <SelectSubjectsListFooter
      class="margin-top-1"
      type="members"
      :count="usersSelected.length"
      :show-role-selector="showRoleSelector"
      @invite="$emit('invite', usersSelected, $event)"
    />
  </div>
</template>

<script>
import SelectSubjectsListFooter from '@baserow_enterprise/components/rbac/SelectSubjectsListFooter'

export default {
  name: 'SelectMembersList',
  components: { SelectSubjectsListFooter },
  props: {
    users: {
      type: Array,
      required: false,
      default: () => [],
    },
    showRoleSelector: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      usersFiltered: this.users,
      usersSelected: [],
      activeSearchTerm: null,
    }
  },
  computed: {
    searchAbleAttributes() {
      return ['name', 'email']
    },
  },
  methods: {
    search(value) {
      if (value === null || value === '' || this.users.length === 0) {
        this.usersFiltered = this.users
      } else {
        const valueSanitised = value.trim().toLowerCase()
        this.usersFiltered = this.users.filter((user) =>
          this.searchAbleAttributes.some((attribute) =>
            user[attribute].toLowerCase().includes(valueSanitised)
          )
        )
      }
    },
    userSelected({ value, item }) {
      if (value) {
        this.usersSelected.push(item)
      } else {
        const index = this.usersSelected.findIndex(
          (user) => user.id === item.id
        )
        this.usersSelected.splice(index, 1)
      }
    },
  },
}
</script>
