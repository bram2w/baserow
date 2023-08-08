import { calculateTempOrder } from '@baserow/modules/core/utils/order'

describe('Order', () => {
  describe('calculateTempOrder', () => {
    it('should return 1 if beforeOrder and afterOrder are null', () => {
      const beforeOrder = null
      const afterOrder = null
      const expected = '1'
      const result = calculateTempOrder(beforeOrder, afterOrder)
      expect(result).toEqual(expected)
    })

    it('should return beforeOrder + 1 if afterOrder is null', () => {
      const beforeOrder = '1'
      const afterOrder = null
      const expected = '2'
      const result = calculateTempOrder(beforeOrder, afterOrder)
      expect(result).toEqual(expected)
    })

    it('should return afterOrder / 2 if beforeOrder is null', () => {
      const beforeOrder = null
      const afterOrder = '2'
      const expected = '1'
      const result = calculateTempOrder(beforeOrder, afterOrder)
      expect(result).toEqual(expected)
    })

    it('should return (beforeOrder + afterOrder) / 2 if beforeOrder and afterOrder are not null', () => {
      const beforeOrder = '1'
      const afterOrder = '3'
      const expected = '2'
      const result = calculateTempOrder(beforeOrder, afterOrder)
      expect(result).toEqual(expected)
    })

    it('should be able to handle numbers with a lot of decimals', () => {
      const beforeOrder = '1.55555555555'
      const afterOrder = '1.577777777777'
      const expected = '1.5666666666635'
      const result = calculateTempOrder(beforeOrder, afterOrder)
      expect(result).toEqual(expected)
    })
  })
})
