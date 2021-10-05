import {
  clone,
  mappingToStringifiedJSONLines,
} from '@baserow/modules/core/utils/object'

describe('test utils object', () => {
  test('test clone', () => {
    const o = {
      a: '1',
      b: '2',
      c: {
        d: '3',
      },
    }
    const cloned = clone(o)

    expect(o !== cloned).toBe(true)
    o.a = '5'
    o.c.d = '6'
    expect(cloned.a).toBe('1')
    expect(cloned.c.d).toBe('3')
  })

  test('test mappingToStringifiedJSONLines', () => {
    expect(
      mappingToStringifiedJSONLines(
        {
          key_1: 'Value 1',
          key_2: 'Value 2',
          key_3: 'Value 3',
        },
        {
          key_1: '',
          key_a: [
            {
              key_b: '',
              key_2: '',
              key_3: '',
              key_c: {
                key_d: {
                  key_1: '',
                  key_e: [
                    {
                      key_3: '',
                    },
                  ],
                },
              },
            },
          ],
          key_2: '',
        }
      )
    ).toMatchObject({
      2: 'Value 1',
      6: 'Value 2',
      10: 'Value 1',
      13: 'Value 3',
      20: 'Value 2',
    })
  })
})
