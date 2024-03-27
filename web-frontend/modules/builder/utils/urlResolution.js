import { compile } from 'path-to-regexp'
import { PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS } from '@baserow/modules/builder/enums'
import { ensureString } from '@baserow/modules/core/utils/validator'

/**
 * Responsible for generating the data necessary to resolve an application builder
 * element URL. Used by LinkElement and LinkField to generate URLs, based on the
 * designer's navigation type / page / url choices.
 *
 * @param {Object} element The element's properties we'll use for generating the URL.
 * @param {Object} builder A builder application.
 * @param {Function} resolveFormula A resolveFormula function we'll use if the
 *  element has page parameters which need to be resolved.
 * @param {String} editorMode A builder application's editor mode.
 * @returns {Object} An object containing a resolved URL, and whether the URL is external.
 */
export default function resolveElementUrl(
  element,
  builder,
  resolveFormula,
  editorMode
) {
  let resolvedUrl = ''
  const resolvedContext = {
    url: '',
    isExternalLink: false,
  }
  if (element.navigation_type === 'page') {
    if (!isNaN(element.navigate_to_page_id)) {
      const page = builder.pages.find(
        ({ id }) => id === element.navigate_to_page_id
      )

      // The builder page list might be empty or the page has been deleted
      if (!page) {
        return resolvedContext
      }

      const paramTypeMap = Object.fromEntries(
        page.path_params.map(({ name, type }) => [name, type])
      )

      const toPath = compile(page.path, { encode: encodeURIComponent })
      const pageParams = Object.fromEntries(
        element.page_parameters.map(({ name, value }) => [
          name,
          PAGE_PARAM_TYPE_VALIDATION_FUNCTIONS[paramTypeMap[name]](
            resolveFormula(value)
          ),
        ])
      )
      resolvedUrl = toPath(pageParams)
    }
  } else {
    resolvedUrl = ensureString(resolveFormula(element.navigate_to_url))
  }
  resolvedContext.url = prefixInternalResolvedUrl(
    resolvedUrl,
    builder,
    element.navigation_type,
    editorMode
  )
  resolvedContext.isExternalLink = isExternalLink(
    resolvedContext.url,
    element.navigation_type
  )
  return resolvedContext
}

/**
 * Responsible for prefixing a resolvedUrl with the builder application's preview
 * URI, if it meets certain conditions.
 *
 * @param {String} resolvedUrl A URL which `resolveElementUrl` has generated.
 * @param {Object} builder A builder application.
 * @param {String} navigationType An element's `navigation_type` (custom / page).
 * @param {String} editorMode A builder application's editor mode.
 * @returns {String} A URL we may have prefixed with the application's preview URI.
 */
export function prefixInternalResolvedUrl(
  resolvedUrl,
  builder,
  navigationType,
  editorMode
) {
  if (
    resolvedUrl &&
    editorMode === 'preview' &&
    (navigationType === 'page' ||
      (navigationType === 'custom' && resolvedUrl.startsWith('/')))
  ) {
    // Add prefix in preview mode for page navigation or custom URL starting with `/`
    return `/builder/${builder.id}/preview${resolvedUrl}`
  } else {
    return resolvedUrl
  }
}

/**
 * Responsible for deciding if the resolvedUrl points to an internal or external source.
 *
 * @param {String} resolvedUrl A URL which `resolveElementUrl` has generated.
 * @param {String} navigationType An element's `navigation_type` (custom / page).
 * @returns {Boolean} Whether this resolvedUrl is external.
 */
export function isExternalLink(resolvedUrl, navigationType) {
  return navigationType === 'custom' && !resolvedUrl.startsWith('/')
}
