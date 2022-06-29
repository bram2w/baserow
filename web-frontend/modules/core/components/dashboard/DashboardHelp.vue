<template>
  <div class="dashboard__help">
    <div class="dashboard__help-title">{{ $t('dashboard.alertTitle') }}</div>
    <p class="dashboard__help-description">
      {{ $t('dashboard.alertText') }}
    </p>
    <a
      href="https://gitlab.com/bramw/baserow"
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
      {{ $t('dashboard.starOnGitlab') }}
      <i class="fab fa-gitlab"></i>
    </a>
    <a
      v-tooltip="$t('dashboard.shareOnTwitter')"
      :href="
        'https://twitter.com/intent/tweet?url=https://baserow.io' +
        '&hashtags=opensource,nocode,database,baserow&text=' +
        encodeURI($t('dashboard.tweetContent'))
      "
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
      <i class="fab fa-twitter"></i>
    </a>
    <a
      v-tooltip="$t('dashboard.shareOnReddit')"
      :href="
        'https://www.reddit.com/submit?url=https://baserow.io&title=' +
        encodeURI($t('dashboard.redditTitle'))
      "
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
      <i class="fab fa-reddit"></i>
    </a>
    <a
      v-tooltip="$t('dashboard.shareOnFacebook')"
      href="https://www.facebook.com/sharer/sharer.php?u=https://baserow.io"
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
      <i class="fab fa-facebook"></i>
    </a>
    <a
      v-tooltip="$t('dashboard.shareOnLinkedIn')"
      href="https://www.linkedin.com/sharing/share-offsite/?url=https://baserow.io"
      target="_blank"
      rel="noopener noreferrer"
      class="button button--primary dashboard__help-button"
    >
      <i class="fab fa-linkedin"></i>
    </a>
  </div>
</template>

<script>
export default {
  name: 'DashboardHelp',
}
</script>
