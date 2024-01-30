<template>
  <div class="presentation">
    <div v-if="image || icon || initials" class="presentation__avatar">
      <Avatar
        :size="iconSize"
        :image="image"
        :icon="icon"
        :initials="initials"
        :color="avatarColor"
        rounded
      />
    </div>
    <div class="presentation__content">
      <div class="presentation__title">{{ title }}</div>
      <div v-if="subtitle" class="presentation__subtitle">{{ subtitle }}</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Presentation',
  props: {
    initials: {
      type: String,
      required: false,
      default: '',
    },
    icon: {
      type: String,
      required: false,
      default: '',
    },
    iconSize: {
      type: String,
      required: false,
      default: 'large',
    },
    image: {
      type: String,
      required: false,
      default: null,
    },
    avatarColor: {
      type: String,
      required: false,
      default: 'blue',
    },
    title: {
      type: String,
      required: true,
      default: '',
    },
    subtitle: {
      type: String,
      required: false,
      default: '',
    },
  },
}
</script>
