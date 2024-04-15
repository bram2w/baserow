<template>
  <div class="dashboard__help">
    <div class="dashboard__help-title">{{ $t('dashboard.alertTitle') }}</div>
    <p class="dashboard__help-description">
      {{ $t('dashboard.alertText') }}
    </p>
    <Button
      type="primary"
      icon="baserow-icon-gitlab"
      tag="a"
      href="https://gitlab.com/baserow/baserow"
      target="_blank"
      rel="noopener noreferrer"
    >
      {{ $t('dashboard.starOnGitlab') }}
    </Button>
    <Button
      v-tooltip="$t('dashboard.shareOnTwitter')"
      type="primary"
      icon="baserow-icon-twitter"
      tag="a"
      :href="`https://twitter.com/intent/tweet?url=https://baserow.io&hashtags=opensource,nocode,database,baserow&text=${encodeURI(
        $t('dashboard.tweetContent')
      )}`"
      target="_blank"
      rel="noopener noreferrer"
    >
    </Button>
    <Button
      v-tooltip="$t('dashboard.shareOnReddit')"
      type="primary"
      tag="a"
      icon="baserow-icon-reddit"
      :href="
        'https://www.reddit.com/submit?url=https://baserow.io&title=' +
        encodeURI($t('dashboard.redditTitle'))
      "
      target="_blank"
      rel="noopener noreferrer"
    >
    </Button>
    <Button
      v-tooltip="$t('dashboard.shareOnFacebook')"
      type="primary"
      tag="a"
      icon="baserow-icon-facebook"
      href="https://www.facebook.com/sharer/sharer.php?u=https://baserow.io"
      target="_blank"
      rel="noopener noreferrer"
    >
    </Button>
    <Button
      v-tooltip="$t('dashboard.shareOnLinkedIn')"
      type="primary"
      tag="a"
      icon="baserow-icon-linkedin"
      href="https://www.linkedin.com/sharing/share-offsite/?url=https://baserow.io"
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
    </Button>
  </div>
</template>

<script>
export default {
  name: 'DashboardHelp',
}
</script>
