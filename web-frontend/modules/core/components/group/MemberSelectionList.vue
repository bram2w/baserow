<template>
  <div>
    <input
      v-model="activeSearchTerm"
      type="text"
      class="input input--large"
      :placeholder="$t('memberSelectionList.searchPlaceholder')"
    />
    <div class="margin-top-2">
      {{
        $t('memberSelectionList.selectedAmountLabel', {
          count: membersSelected.length,
        })
      }}
    </div>
    <List
      class="margin-top-2 select-members-list__items"
      :items="membersFiltered"
      :attributes="['email']"
      selectable
      @selected="memberSelected"
    >
      <template #left-side="{ item }">
        <div class="select-members-list__user-initials margin-left-1">
          {{ item.name | nameAbbreviation }}
        </div>
        <span class="margin-left-1">
          {{ item.name }}
        </span>
      </template>
    </List>
    <MemberAssignmentModalFooter
      :count="membersSelected.length"
      @invite="$emit('invite', membersSelected)"
    />
  </div>
</template>

<script>
import MemberAssignmentModalFooter from '@baserow/modules/core/components/group/MemberAssignmentModalFooter'
export default {
  name: 'MemberSelectionList',
  components: { MemberAssignmentModalFooter },
  props: {
    members: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      membersFiltered: this.members,
      membersSelected: [],
      activeSearchTerm: null,
    }
  },
  computed: {
    searchAbleAttributes() {
      return ['name', 'email']
    },
  },
  watch: {
    activeSearchTerm(newValue) {
      this.search(newValue)
    },
  },
  methods: {
    search(value) {
      if (value === null || value === '' || this.members.length === 0) {
        this.membersFiltered = this.members
      }

      this.membersFiltered = this.members.filter((member) =>
        this.searchAbleAttributes.some((attribute) =>
          member[attribute].toLowerCase().includes(value.toLowerCase())
        )
      )
    },
    memberSelected({ value, item }) {
      if (value) {
        this.membersSelected.push(item)
      } else {
        const index = this.membersSelected.findIndex(
          (member) => member.id === item.id
        )
        this.membersSelected.splice(index, 1)
      }
    },
  },
}
</script>
