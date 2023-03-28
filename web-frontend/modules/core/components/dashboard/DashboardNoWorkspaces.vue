<template>
  <div class="placeholder placeholder--align-left margin-top-0">
    <div class="placeholder__icon">
      <i class="fas fa-layer-group"></i>
    </div>
    <h1 class="placeholder__title">{{ $t('dashboard.noWorkspaceTitle') }}</h1>
    <p v-if="$hasPermission('create_workspace')" class="placeholder__content">
      {{ $t('dashboard.noWorkspaceText') }}
    </p>
    <p v-else class="placeholder__content">
      {{ $t('dashboard.noWorkspaceTextWithoutCreatePermission') }}
    </p>
    <div class="placeholder__action">
      <a
        v-if="$hasPermission('create_workspace')"
        class="button button--large"
        @click="$emit('create-clicked')"
      >
        <i class="fas fa-plus"></i>
        {{ $t('dashboard.createWorkspace') }}
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DashboardNoWorkspaces',
}
</script>
