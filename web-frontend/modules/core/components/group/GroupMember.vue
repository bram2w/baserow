<template>
  <div
    ref="member"
    class="group-member"
    :class="{ 'group-member--highlight': highlighted }"
  >
    <div class="group-member__initials">{{ name | nameAbbreviation }}</div>
    <div class="group-member__content">
      <div class="group-member__name">
        {{ name }}
      </div>
      <div class="group-member__description">
        {{ description }}
      </div>
    </div>
    <div class="group-member__permissions">
      <Dropdown
        v-if="!disabled"
        :value="permissions"
        :show-search="false"
        @input="$emit('updated', { permissions: $event })"
      >
        <DropdownItem
          :name="$t('permission.admin')"
          value="ADMIN"
          :description="$t('permission.adminDescription')"
        ></DropdownItem>
        <DropdownItem
          :name="$t('permission.member')"
          value="MEMBER"
          :description="$t('permission.memberDescription')"
        ></DropdownItem>
      </Dropdown>
    </div>
    <div class="group-member__actions">
      <a
        v-if="!disabled"
        class="group-member__action"
        :class="{ 'group-member__action--loading': loading }"
        @click="$emit('removed')"
      >
        <i class="fa fa-trash"></i>
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'GroupMember',
  props: {
    id: {
      type: Number,
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: true,
    },
    permissions: {
      type: String,
      required: true,
    },
    loading: {
      type: Boolean,
      required: false,
      default: false,
    },
    disabled: {
      type: Boolean,
      required: false,
      default: false,
    },
  },
  data() {
    return {
      highlighted: false,
    }
  },
  methods: {
    highlight() {
      this.$refs.member.scrollIntoView({ behavior: 'smooth' })
      this.highlighted = true
      setTimeout(() => {
        this.highlighted = false
      }, 2000)
    },
  },
}
</script>
