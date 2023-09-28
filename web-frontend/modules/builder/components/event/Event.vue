<template>
  <Expandable toggle-on-click>
    <template #header="{ toggle, expanded }">
      <div class="event__header">
        <div class="event__label">{{ event.label }}</div>
        <a class="event__toggle" @click.stop="toggle">
          <i :class="getIcon(expanded)"></i>
        </a>
      </div>
    </template>
    <template #default>
      This is where you will be able to define your actions in the future :)
    </template>
  </Expandable>
</template>

<script>
import { Event } from '@baserow/modules/builder/eventTypes'

export default {
  name: 'Event',
  props: {
    event: {
      type: Event,
      required: true,
    },
  },
  methods: {
    getIcon(expanded) {
      return expanded ? 'iconoir-nav-arrow-down' : 'iconoir-nav-arrow-right'
    },
  },
}
</script>
