<template>
  <li class="tree__sub">
    <a class="tree__sub-link tree__sub-link--disabled">
      {{ jobSidebarText }}
      <div class="tree__progress-percentage">
        {{ job.progress_percentage }} %
      </div>
    </a>
    <div class="tree__sub-link--loading"></div>
  </li>
</template>

<script>
export default {
  name: 'SidebarItemPendingJob',
  props: {
    job: {
      type: Object,
      required: true,
    },
  },
  computed: {
    jobSidebarText() {
      return this.$registry.get('job', this.job.type).getSidebarText(this.job)
    },
  },
}
</script>
