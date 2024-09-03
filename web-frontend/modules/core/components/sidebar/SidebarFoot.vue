<template>
  <div class="sidebar__section sidebar__section--bottom">
    <div class="sidebar__foot">
      <div class="sidebar__logo">
        <ExternalLinkBaserowLogo />
      </div>
      <div class="sidebar__foot-links">
        <a
          class="sidebar__foot-link"
          :class="{
            'sidebar__foot-link--loading': undoLoading,
          }"
          @click="undo(false)"
        >
          <i class="sidebar__foot-link-icon iconoir-undo"></i>
        </a>
        <a
          class="sidebar__foot-link"
          :class="{
            'sidebar__foot-link--loading': redoLoading,
          }"
          @click="redo(false)"
        >
          <i class="sidebar__foot-link-icon iconoir-redo"></i>
        </a>
      </div>
    </div>
  </div>
</template>

<script>
import undoRedo from '@baserow/modules/core/mixins/undoRedo'
import ExternalLinkBaserowLogo from '@baserow/modules/core/components/ExternalLinkBaserowLogo'

export default {
  name: 'SidebarFoot',
  components: { ExternalLinkBaserowLogo },
  mixins: [undoRedo],
}
</script>
