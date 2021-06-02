<template>
  <div class="user-admin-group" v-on="$listeners">
    <div ref="groupsContainer" class="user-admin-group__container">
      <span ref="empty" class="user-admin-group__empty-item"></span>
      <span
        v-for="(group, index) in groups"
        ref="groups"
        :key="'admin-row-group' + userId + '-' + group.id"
        class="user-admin-group__item"
        :style="{
          order: index,
        }"
      >
        {{ group[nameKey] }}
        <i
          v-if="group.permissions == 'ADMIN'"
          v-tooltip="'is group admin'"
          class="user-admin-group__icon fas fa-users-cog"
        ></i>
      </span>
      <a
        v-show="overflowing"
        ref="expand"
        class="user-admin-group__expand"
        :style="{
          order: expandOrder,
        }"
        @click.prevent="showContext"
        >+{{ numHiddenGroups }}</a
      >
    </div>
  </div>
</template>
<script>
import ResizeObserver from 'resize-observer-polyfill'

/**
 * Displays a list of a users groups with a modal displaying any groups that do not fit.
 * Adds an icon showing if the user is an admin of the group.
 */
export default {
  name: 'UserGroupsField',
  props: {
    row: {
      required: true,
      type: Object,
    },
    column: {
      required: true,
      type: Object,
    },
  },
  data() {
    return {
      eventName: 'show-hidden-groups',
      nameKey: 'name',
      overflowing: false,
      numHiddenGroups: 0,
      renderContext: false,
      expandOrder: -1,
    }
  },
  computed: {
    hiddenGroups() {
      return this.groups.slice(this.groups.length - this.numHiddenGroups)
    },
    groups() {
      return this.row[this.column.key]
    },
    userId() {
      return this.row.id
    },
  },
  mounted() {
    this.$el.resizeObserver = new ResizeObserver(this.recalculateHiddenGroups)
    this.$el.resizeObserver.observe(this.$el)
  },
  beforeDestroy() {
    this.$el.resizeObserver.unobserve(this.$el)
  },
  created() {
    this.recalculateHiddenGroups()
  },
  methods: {
    showContext(event) {
      this.$emit(this.eventName, {
        hiddenValues: this.hiddenGroups,
        target: event.currentTarget,
        time: Date.now(),
      })
    },
    /**
     * Calculates how many groups fit into the groups cell, if any are overflowing and
     * do not fit we add a + button to display a context menu showing these hidden
     * groups. We rely on flexbox wrapping to make groups which do not fit in the cell
     * wrap down to a new row below which is invisible.
     */
    recalculateHiddenGroups() {
      if (process.server) {
        return
      }

      this.$nextTick(() => {
        let expandOrder = 0
        let numHiddenGroups = this.groups.length

        /*
         The starting empty element never flex-wraps down into a new row as it has 0
         width.
         If an element after it has the same top value then it must not have wrapped
         down and hence must fit and be visible. If the elements top value is greater
         then it must have overflowed and wrapped into a row below, causing it to
         become invisible.
         Comparing top values is done instead of trying to
         manually calculate which groups fit using el.client/scrollWidth because:
         1. We don't want to worry about exactly calculating the widths of each group
            as there are possibly bugs with this in Vue (scrollWidth etc can return
            invalid numbers in some unknown situations).
         2. By using the tops we leave it entirely up to CSS and the DOM to figure out
            what fits or not reducing the complexity of this method. We don't want
            to try and replicate the overflow calculations ourselves as then we need
            to maintain code that matches the browser calculation in every possible
            situation.
        */
        const emptyElementTop = this.$refs.empty.getBoundingClientRect().top

        // The groups will be null when the user has no groups.
        if (this.$refs.groups) {
          for (let i = 0; i < this.$refs.groups.length; i++) {
            const groupEl = this.$refs.groups[i]
            const groupTop = groupEl.getBoundingClientRect().top
            if (groupTop > emptyElementTop) {
              /*
             This groupEl element has been flex-wrapped down into a new row due to no
             space. Every group after this one must also be hidden hence we now have
             calculated the number of hidden groups and can break.

             Insert the expand button before this hidden group. This button might also
             wrap down and become invisible hence we later on recheck if this has
             happened or not.
            */
              expandOrder = i - 1
              break
            } else {
              // Insert the expand button after the latest visible group
              expandOrder = i
              numHiddenGroups--
            }
          }
        }

        this.expandOrder = expandOrder
        this.numHiddenGroups = numHiddenGroups
        this.overflowing = numHiddenGroups !== 0

        /*
         Check that the expand button hasn't wrapped down and become invisible because
         there wasn't enough room to fit it on the first row. If so move it back one
         further in the order so it replaces the last visible group in the row instead
        */
        if (this.overflowing) {
          /*
           We have to wait a tick for the DOM to recalculate to see if the inserted
           expand button fits or not. This is much easier, simpler and cleaner
           than attempting to do the calculation CSS/DOM will do for us ourselves!
          */
          this.$nextTick(() => {
            const emptyElementTop = this.$refs.empty.getBoundingClientRect().top
            const expandTop = this.$refs.expand.getBoundingClientRect().top
            if (expandTop > emptyElementTop) {
              this.expandOrder--
              // By moving the button back one we will make the last group overflow,
              // wrap and become invisible so we update numHiddenGroups accordingly.
              this.numHiddenGroups++
            }
          })
        }
      })
    },
  },
}
</script>
