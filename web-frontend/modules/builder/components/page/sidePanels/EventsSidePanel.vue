<template>
  <div>
    <Event
      v-for="event in elementType.getEvents()"
      :key="event.getType()"
      :event="event"
      class="margin-bottom-2"
    ></Event>
  </div>
</template>

<script>
import elementSidePanel from '@baserow/modules/builder/mixins/elementSidePanel'
import Event from '@baserow/modules/builder/components/event/Event.vue'

export default {
  name: 'EventSidePanel',
  components: { Event },
  mixins: [elementSidePanel],
}
</script>
