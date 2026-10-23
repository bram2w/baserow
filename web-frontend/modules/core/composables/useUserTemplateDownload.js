import { ref } from 'vue'
import { useNuxtApp, useRuntimeConfig } from '#app'

import TemplateService from '@baserow/modules/core/services/template'
import { triggerDownload } from '@baserow/modules/core/utils/download'
import { notifyIf } from '@baserow/modules/core/utils/error'

/**
 * Downloads the file of a user template. Its URL is fetched at the click, so that
 * the access is checked then, and isn't kept. The downloads are tracked per
 * template, so that one row's download doesn't block or show on another row.
 */
export function useUserTemplateDownload() {
  const { $client, $i18n, $store } = useNuxtApp()
  const config = useRuntimeConfig()

  // The ids of the templates that are being downloaded.
  const downloadingIds = ref(new Set())

  function isDownloading(template) {
    return downloadingIds.value.has(template.id)
  }

  /**
   * @returns {Promise<boolean>} Whether this call downloaded the template. A second
   *   click while it's downloaded, for example with the keyboard, doesn't download
   *   it twice.
   */
  async function download(template, { latest = false } = {}) {
    if (isDownloading(template)) {
      return false
    }
    downloadingIds.value.add(template.id)
    try {
      const { data } = await TemplateService($client).download(template.slug, {
        latest,
      })
      await save(data)
    } catch (error) {
      notifyIf(error, 'template')
    } finally {
      downloadingIds.value.delete(template.id)
    }
    return true
  }

  async function save({ url, file_name: filename }) {
    try {
      await triggerDownload(url, filename, {
        viaXhr: `${config.public.downloadFileViaXhr}` === '1',
      })
    } catch (error) {
      // The file couldn't be fetched from the storage.
      await $store.dispatch('toast/error', {
        title: $i18n.t('clientHandler.notCompletedTitle'),
        message: $i18n.t('clientHandler.notCompletedDescription'),
      })
    }
  }

  return { isDownloading, download }
}
