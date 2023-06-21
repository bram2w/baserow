import { getFilesFromEvent } from '@baserow/modules/core/utils/file'

describe('getFilesFromEvent', () => {
  test('submit files via upload input', () => {
    const files = ['file1', 'file2']
    const event = { target: { files } }
    expect(getFilesFromEvent(event)).toEqual(files)
  })

  test('submit files via drag and drop', () => {
    const files = ['file1', 'file2']
    const event = { dataTransfer: { files } }
    expect(getFilesFromEvent(event)).toEqual(files)
  })

  test('submit no files', () => {
    const files = []
    const event = { dataTransfer: { files } }
    expect(getFilesFromEvent(event)).toEqual(files)
  })
})
