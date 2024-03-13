import { resolveFormula } from '@baserow/modules/core/formula'
import resolveElementUrl from '@baserow/modules/builder/utils/urlResolution'

describe('resolveElementUrl tests', () => {
  test('Should return empty resolvedContext with page navigation type where page is not found.', () => {
    const element = {
      navigation_type: 'page',
      navigate_to_page_id: 42,
    }
    const builder = { pages: [{ id: 1 }] }

    const result = resolveElementUrl(
      element,
      builder,
      resolveFormula,
      'preview'
    )
    expect(result).toEqual({ url: '', isExternalUrl: false })
  })
  test('Should return resolvedContext with page navigation type where page is found and has no params.', () => {
    const element = {
      navigation_type: 'page',
      navigate_to_page_id: 1,
      page_parameters: [],
    }
    const builder = {
      id: 123,
      pages: [{ id: 1, path: '/contact-us/', path_params: [] }],
    }

    const result = resolveElementUrl(
      element,
      builder,
      resolveFormula,
      'preview'
    )
    expect(result).toEqual({
      url: '/builder/123/preview/contact-us/',
      isExternalUrl: false,
    })
  })
  test('Should return resolvedContext with page navigation type where page is found and has params.', () => {
    const element = {
      navigation_type: 'page',
      navigate_to_page_id: 1,
      page_parameters: [{ name: 'id', value: "'10'" }],
    }
    const builder = {
      id: 123,
      pages: [
        {
          id: 1,
          path: '/product/:id/',
          path_params: [{ name: 'id', type: 'numeric' }],
        },
      ],
    }

    const result = resolveElementUrl(
      element,
      builder,
      resolveFormula,
      'preview'
    )
    expect(result).toEqual({
      url: '/builder/123/preview/product/10/',
      isExternalUrl: false,
    })
  })
  test('Should return resolvedContext for external custom navigation type.', () => {
    const element = {
      navigation_type: 'custom',
      navigate_to_url: "'https://baserow.io'",
    }
    const builder = { pages: [] }

    const result = resolveElementUrl(
      element,
      builder,
      resolveFormula,
      'preview'
    )
    expect(result).toEqual({
      url: 'https://baserow.io',
      isExternalUrl: true,
    })
  })
  test('Should return resolvedContext for internal custom navigation type.', () => {
    const element = {
      navigation_type: 'custom',
      navigate_to_url: "'/contact/'",
    }
    const builder = { id: 123, pages: [] }

    const result = resolveElementUrl(
      element,
      builder,
      resolveFormula,
      'preview'
    )
    expect(result).toEqual({
      url: '/builder/123/preview/contact/',
      isExternalUrl: false,
    })
  })
})
