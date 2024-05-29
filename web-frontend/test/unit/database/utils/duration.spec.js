import {
  parseDurationValue,
  formatDurationValue,
  roundDurationValueToFormat,
} from '@baserow/modules/database/utils/duration'

const SECS_IN_MIN = 60
const SECS_IN_HOUR = 60 * 60

const VALID_DURATION_VALUES = {
  'd h': [
    ['1d 2h', 26 * SECS_IN_HOUR],
    ['2 1h', 49 * SECS_IN_HOUR],
    ['2 2', 50 * SECS_IN_HOUR],
    ['1 8', 32 * SECS_IN_HOUR],
    ['1d0h', 24 * SECS_IN_HOUR],
    ['1d25', 49 * SECS_IN_HOUR],
    ['5h', 5 * SECS_IN_HOUR],
    ['2d', 48 * SECS_IN_HOUR],
    ['10', 10 * SECS_IN_HOUR],
    ['3600.0', 1 * SECS_IN_HOUR],
    ['60:0.0', 1 * SECS_IN_HOUR],
    ['1d 2h 3m', 26 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['1d 2h 58m', 26 * SECS_IN_HOUR + 58 * SECS_IN_MIN],
    ['1d 3m', 24 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['0', 0],
    ['-1 3:05', -((24 + 3) * SECS_IN_HOUR + 5 * SECS_IN_MIN)],
    ['-1h 3m05s', -(3600 + 3 * SECS_IN_MIN + 5)],
  ],
  'd h:mm': [
    ['1d 2:30', 26 * SECS_IN_HOUR + 30 * 60],
    ['2 1:30', 49 * SECS_IN_HOUR + 30 * 60],
    ['2 1:61', 50 * SECS_IN_HOUR + 1 * 60],
    ['1 8:30', 32 * SECS_IN_HOUR + 30 * 60],
    ['1d0:61', 25 * SECS_IN_HOUR + 1 * 60],
    ['1d0:30', 24 * SECS_IN_HOUR + 30 * 60],
    ['1d1:30', 25 * SECS_IN_HOUR + 30 * 60],
    ['5:30', 5 * SECS_IN_HOUR + 30 * 60],
    ['10:30', 10 * SECS_IN_HOUR + 30 * 60],
    ['1d 2h 3m', 26 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['1d 2h 3m 4s', 26 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 4],
    ['1d 3m', 24 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['1d 32s', 24 * SECS_IN_HOUR + 32], // rounded up to 1m
    ['0:30', 30 * 60],
    ['0:0', 0],
    ['-1 3:05', -((24 + 3) * SECS_IN_HOUR + 5 * SECS_IN_MIN)],
    ['-1h 3m05s', -(3600 + 3 * SECS_IN_MIN + 5)],
  ],
  'd h:mm:ss': [
    ['1d 2:30:45', 26 * SECS_IN_HOUR + 30 * 60 + 45],
    ['2 2:30:45', 50 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1 8:30:45', 32 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1d0:30:45', 24 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1d1:30:45', 25 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1d2:30:61', 26 * SECS_IN_HOUR + 31 * 60 + 1],
    ['5:30:45', 5 * SECS_IN_HOUR + 30 * 60 + 45],
    ['10:30:45', 10 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1d 2h 3m 4s', 26 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 4],
    ['1d 2h 3m', 26 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['1d 3m', 24 * SECS_IN_HOUR + 3 * SECS_IN_MIN],
    ['0:30:45', 30 * 60 + 45],
    ['0:0:45', 45],
    ['0:0:0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
    ['-1h 3m05s', -(3600 + 3 * SECS_IN_MIN + 5)],
    ['-1d 3:05:01', -((24 + 3) * SECS_IN_HOUR + 5 * SECS_IN_MIN + 1)],
  ],
  'h:mm': [
    ['2:30', 2 * SECS_IN_HOUR + 30 * 60],
    ['1:30', 1 * SECS_IN_HOUR + 30 * 60],
    ['2:30', 2 * SECS_IN_HOUR + 30 * 60],
    ['8:30', 8 * SECS_IN_HOUR + 30 * 60],
    ['0:30', 30 * 60],
    ['0:61', 61 * 60],
    ['1d 4h 50m 37s', (24 + 4) * SECS_IN_HOUR + 50 * SECS_IN_MIN + 37], // rounded up to +1 min
    ['0:0', 0],
    ['0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)], // lower denominator
    ['-1h 3m05s', -(3600 + 3 * SECS_IN_MIN + 5)],
    ['-1d 1h 3m05s', -(25 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
  'h:mm:ss': [
    ['2:30:45', 2 * SECS_IN_HOUR + 30 * 60 + 45],
    ['1:30:45', 1 * SECS_IN_HOUR + 30 * 60 + 45],
    ['2:30:45', 2 * SECS_IN_HOUR + 30 * 60 + 45],
    ['8:30:45', 8 * SECS_IN_HOUR + 30 * 60 + 45],
    ['0:30:45', 30 * 60 + 45],
    ['1d 4h 50m 37.7s', (24 + 4) * SECS_IN_HOUR + 50 * SECS_IN_MIN + 37.7], // rouded up to +1min
    ['0:0:45', 45],
    ['0:0:61', 61],
    ['0:0:0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
  'h:mm:ss.s': [
    ['2:30:45.1', 2 * SECS_IN_HOUR + 30 * 60 + 45.1],
    ['1:30:45.2', 1 * SECS_IN_HOUR + 30 * 60 + 45.2],
    ['2:30:45.3', 2 * SECS_IN_HOUR + 30 * 60 + 45.3],
    ['8:30:45.9', 8 * SECS_IN_HOUR + 30 * 60 + 45.9],
    ['1d 4h 50m 37.28s', (24 + 4) * SECS_IN_HOUR + 50 * SECS_IN_MIN + 37.28],
    ['0:30:45.5', 30 * 60 + 45.5],
    ['0:0:45.0', 45],
    ['0:0:59.9', 59.9],
    ['0:0:0.0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
  'h:mm:ss.ss': [
    ['2:30:45.11', 2 * SECS_IN_HOUR + 30 * 60 + 45.11],
    ['1:30:45.22', 1 * SECS_IN_HOUR + 30 * 60 + 45.22],
    ['2:30:45.33', 2 * SECS_IN_HOUR + 30 * 60 + 45.33],
    ['8:30:45.46', 8 * SECS_IN_HOUR + 30 * 60 + 45.46],
    ['1d 4h 50m 37.28s', (24 + 4) * SECS_IN_HOUR + 50 * SECS_IN_MIN + 37.28],
    ['0:30:45.50', 30 * 60 + 45.5],
    ['0:0:45.00', 45],
    ['0:0:59.99', 59.99],
    ['0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
  'h:mm:ss.sss': [
    ['2:30:45.111', 2 * SECS_IN_HOUR + 30 * 60 + 45.111],
    ['1:30:45.222', 1 * SECS_IN_HOUR + 30 * 60 + 45.222],
    ['2:30:45.333', 2 * SECS_IN_HOUR + 30 * 60 + 45.333],
    ['8:30:45.456', 8 * SECS_IN_HOUR + 30 * 60 + 45.456],
    ['1d 4h 50m 37.283s', (24 + 4) * SECS_IN_HOUR + 50 * SECS_IN_MIN + 37.283],
    ['0:30:45.500', 30 * 60 + 45.5],
    ['0:0:45.000', 45],
    ['0:0:59.999', 59.999],
    ['0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
  'd h mm ss': [
    ['2d 4h 3m 4s', (2 * 24 + 4) * SECS_IN_HOUR + 30 * SECS_IN_MIN + 4],
    ['4m 12.3s', 4 * SECS_IN_MIN + 12.3],
    ['8:30:45.589', 8 * SECS_IN_HOUR + 30 * 60 + 46],
    ['0:0:45.000', 45],
    ['0:0:59.999', 59.999],
    ['0', 0],
    ['-1 3:05', -(24 * SECS_IN_HOUR + 3 * SECS_IN_MIN + 5)],
  ],
}

const INVALID_DURATION_VALUES = [
  'd',
  'h',
  '1day',
  '2 days',
  '1 hour',
  '8 hours',
  '1:2:3:4',
  'aaaaa',
  '1dd',
  '2hh',
  '-1d -3h',
  '-1d -3:04',
]

const DURATION_FORMATTED_VALUES = {
  'd h': [
    [0, '0d 0h'],
    [1 * SECS_IN_HOUR, '0d 1h'],
    [24 * SECS_IN_HOUR, '1d 0h'],
    [25 * SECS_IN_HOUR, '1d 1h'],
    [49 * SECS_IN_HOUR, '2d 1h'],
    [50 * SECS_IN_HOUR, '2d 2h'],
    [32 * SECS_IN_HOUR, '1d 8h'],
    [5 * SECS_IN_HOUR, '0d 5h'],
    [-(25 * SECS_IN_HOUR), '-1d 1h'],
  ],
  'd h:mm': [
    [0, '0d 0:00'],
    [1 * SECS_IN_HOUR, '0d 1:00'],
    [24 * SECS_IN_HOUR, '1d 0:00'],
    [2 * SECS_IN_HOUR, '0d 2:00'],
    [49 * SECS_IN_HOUR, '2d 1:00'],
    [50 * SECS_IN_HOUR, '2d 2:00'],
    [32 * SECS_IN_HOUR, '1d 8:00'],
    [5 * SECS_IN_HOUR, '0d 5:00'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '0d 5:30'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN), '-1d 1:25'],
  ],
  'd h:mm:ss': [
    [0, '0d 0:00:00'],
    [1 * SECS_IN_HOUR, '0d 1:00:00'],
    [24 * SECS_IN_HOUR, '1d 0:00:00'],
    [25 * SECS_IN_HOUR, '1d 1:00:00'],
    [49 * SECS_IN_HOUR, '2d 1:00:00'],
    [50 * SECS_IN_HOUR, '2d 2:00:00'],
    [32 * SECS_IN_HOUR, '1d 8:00:00'],
    [5 * SECS_IN_HOUR, '0d 5:00:00'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '0d 5:30:00'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5, '0d 5:05:05'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6), '-1d 1:25:06'],
  ],
  'h:mm': [
    [0, '0:00'],
    [1 * SECS_IN_MIN, '0:01'],
    [61 * SECS_IN_MIN, '1:01'],
    [24 * SECS_IN_HOUR, '24:00'],
    [25 * SECS_IN_HOUR, '25:00'],
    [49 * SECS_IN_HOUR, '49:00'],
    [50 * SECS_IN_HOUR, '50:00'],
    [32 * SECS_IN_HOUR, '32:00'],
    [5 * SECS_IN_HOUR, '5:00'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '5:30'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6), '-25:25'],
  ],
  'h:mm:ss': [
    [0, '0:00:00'],
    [1, '0:00:01'],
    [61, '0:01:01'],
    [1 * SECS_IN_MIN, '0:01:00'],
    [61 * SECS_IN_MIN, '1:01:00'],
    [24 * SECS_IN_HOUR, '24:00:00'],
    [25 * SECS_IN_HOUR, '25:00:00'],
    [49 * SECS_IN_HOUR, '49:00:00'],
    [50 * SECS_IN_HOUR, '50:00:00'],
    [32 * SECS_IN_HOUR, '32:00:00'],
    [5 * SECS_IN_HOUR, '5:00:00'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '5:30:00'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5, '5:05:05'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6), '-25:25:06'],
  ],
  'h:mm:ss.s': [
    [0, '0:00:00.0'],
    [1.1, '0:00:01.1'],
    [61.9, '0:01:01.9'],
    [1 * SECS_IN_MIN + 1.1, '0:01:01.1'],
    [61 * SECS_IN_MIN + 2.2, '1:01:02.2'],
    [24 * SECS_IN_HOUR + 3.3, '24:00:03.3'],
    [25 * SECS_IN_HOUR + 9.9, '25:00:09.9'],
    [49 * SECS_IN_HOUR, '49:00:00.0'],
    [50 * SECS_IN_HOUR, '50:00:00.0'],
    [32 * SECS_IN_HOUR, '32:00:00.0'],
    [5 * SECS_IN_HOUR, '5:00:00.0'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '5:30:00.0'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5, '5:05:05.0'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5.1, '5:05:05.1'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6), '-25:25:06.0'],
  ],
  'h:mm:ss.ss': [
    [0, '0:00:00.00'],
    [1.11, '0:00:01.11'],
    [61.22, '0:01:01.22'],
    [1 * SECS_IN_MIN + 1.11, '0:01:01.11'],
    [61 * SECS_IN_MIN + 2.22, '1:01:02.22'],
    [24 * SECS_IN_HOUR + 3.33, '24:00:03.33'],
    [25 * SECS_IN_HOUR + 9.99, '25:00:09.99'],
    [49 * SECS_IN_HOUR, '49:00:00.00'],
    [50 * SECS_IN_HOUR, '50:00:00.00'],
    [32 * SECS_IN_HOUR, '32:00:00.00'],
    [5 * SECS_IN_HOUR, '5:00:00.00'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '5:30:00.00'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5, '5:05:05.00'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5.1, '5:05:05.10'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6), '-25:25:06.00'],
  ],
  'h:mm:ss.sss': [
    [0, '0:00:00.000'],
    [1.111, '0:00:01.111'],
    [61.222, '0:01:01.222'],
    [1 * SECS_IN_MIN + 1.111, '0:01:01.111'],
    [61 * SECS_IN_MIN + 2.222, '1:01:02.222'],
    [24 * SECS_IN_HOUR + 3.333, '24:00:03.333'],
    [25 * SECS_IN_HOUR + 9.999, '25:00:09.999'],
    [49 * SECS_IN_HOUR, '49:00:00.000'],
    [50 * SECS_IN_HOUR, '50:00:00.000'],
    [32 * SECS_IN_HOUR, '32:00:00.000'],
    [5 * SECS_IN_HOUR, '5:00:00.000'],
    [5 * SECS_IN_HOUR + 30 * SECS_IN_MIN, '5:30:00.000'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5, '5:05:05.000'],
    [5 * SECS_IN_HOUR + 5 * SECS_IN_MIN + 5.1, '5:05:05.100'],
    [-(25 * SECS_IN_HOUR + 25 * SECS_IN_MIN + 6.001), '-25:25:06.001'],
  ],
}

const DURATION_ROUNDING_VALUES = {
  'd h': [
    [null, null],
    [0, 0],
    [1.9, 0],
    [30, 0],
    [60, 0],
    [29 * SECS_IN_MIN, 0],
    [30 * SECS_IN_MIN, 1 * SECS_IN_HOUR],
    [59 * SECS_IN_MIN, 1 * SECS_IN_HOUR],
    [1 * SECS_IN_HOUR + 29 * SECS_IN_MIN, 1 * SECS_IN_HOUR],
    [1 * SECS_IN_HOUR + 30 * SECS_IN_MIN, 2 * SECS_IN_HOUR],
    [-(25 * SECS_IN_HOUR + 45 * SECS_IN_MIN + 6.001), -26 * SECS_IN_HOUR],
  ],
  'd h:mm': [
    [null, null],
    [0, 0],
    [1, 0],
    [29, 0],
    [30, 1 * SECS_IN_MIN],
    [59, 1 * SECS_IN_MIN],
    [29 * SECS_IN_MIN + 29.9, 29 * SECS_IN_MIN],
    [29 * SECS_IN_MIN + 30, 30 * SECS_IN_MIN],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.001),
      -(25 * SECS_IN_HOUR + 36 * SECS_IN_MIN),
    ],
  ],
  'd h:mm:ss': [
    [null, null],
    [0, 0],
    [0.499, 0],
    [0.5, 1],
    [0.9, 1],
    [1, 1],
    [1.5, 2],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.001),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46),
    ],
  ],
  'h:mm': [
    [null, null],
    [0, 0],
    [1, 0],
    [29, 0],
    [30, 1 * SECS_IN_MIN],
    [59, 1 * SECS_IN_MIN],
    [29 * SECS_IN_MIN + 29.9, 29 * SECS_IN_MIN],
    [29 * SECS_IN_MIN + 30, 30 * SECS_IN_MIN],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.001),
      -(25 * SECS_IN_HOUR + 36 * SECS_IN_MIN),
    ],
  ],
  'h:mm:ss': [
    [null, null],
    [0, 0],
    [0.499, 0],
    [0.5, 1],
    [0.9, 1],
    [1, 1],
    [1.5, 2],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.001),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46),
    ],
  ],
  'h:mm:ss.s': [
    [null, null],
    [0, 0],
    [0.449, 0.4],
    [0.45, 0.5],
    [0.99, 1],
    [1.12, 1.1],
    [1.9, 1.9],
    [1.99, 2],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.001),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.0),
    ],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.068),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.1),
    ],
  ],
  'h:mm:ss.ss': [
    [null, null],
    [0, 0],
    [0.49, 0.49],
    [0.494, 0.49],
    [0.499, 0.5],
    [0.999, 1],
    [1.123, 1.12],
    [1.99, 1.99],
    [1.999999, 2],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.068),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.07),
    ],
  ],
  'h:mm:ss.sss': [
    [null, null],
    [0, 0],
    [0.4994, 0.499],
    [0.4995, 0.5],
    [0.9991, 0.999],
    [0.9995, 1],
    [1.123, 1.123],
    [1.999, 1.999],
    [1.999999, 2],
    [
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.068),
      -(25 * SECS_IN_HOUR + 35 * SECS_IN_MIN + 46.068),
    ],
  ],
}

describe('Duration field type utilities', () => {
  describe('parse format: d h', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['d h']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'd h')).toBe(expected)
      })
    }
  })
  describe('parse format: d h:mm', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['d h:mm']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'd h:mm')).toBe(expected)
      })
    }
  })
  describe('parse format: d h:mm:ss', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['d h:mm:ss']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'd h:mm:ss')).toBe(expected)
      })
    }
  })
  describe('parse format: h:mm', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['h:mm']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'h:mm')).toBe(expected)
      })
    }
  })
  describe('parse format: h:mm:ss', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['h:mm:ss']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'h:mm:ss')).toBe(expected)
      })
    }
  })
  describe('parse format: h:mm:ss.s', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['h:mm:ss.s']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'h:mm:ss.s')).toBe(expected)
      })
    }
  })
  describe('parse format: h:mm:ss.ss', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['h:mm:ss.ss']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'h:mm:ss.ss')).toBe(expected)
      })
    }
  })
  describe('parse format: h:mm:ss.sss', () => {
    for (const [input, expected] of VALID_DURATION_VALUES['h:mm:ss.sss']) {
      test(`"${input}" should be parsed to ${expected}`, () => {
        expect(parseDurationValue(input, 'h:mm:ss.sss')).toBe(expected)
      })
    }
  })
  describe('parse invalid values', () => {
    for (const input of INVALID_DURATION_VALUES) {
      test(`"${input}" should be parsed to null`, () => {
        expect(parseDurationValue(input, 'h:mm:ss.sss')).toBe(null)
      })
    }
  })

  describe('format format: d h', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['d h']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'd h')).toBe(expected)
      })
    }
  })

  describe('format format: d h:mm', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['d h:mm']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'd h:mm')).toBe(expected)
      })
    }
  })

  describe('format format: d h:mm:ss', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['d h:mm:ss']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'd h:mm:ss')).toBe(expected)
      })
    }
  })

  describe('format format: h:mm', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['h:mm']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'h:mm')).toBe(expected)
      })
    }
  })

  describe('format format: h:mm:ss', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['h:mm:ss']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'h:mm:ss')).toBe(expected)
      })
    }
  })

  describe('format format: h:mm:ss.s', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['h:mm:ss.s']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'h:mm:ss.s')).toBe(expected)
      })
    }
  })

  describe('format format: h:mm:ss.ss', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['h:mm:ss.ss']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'h:mm:ss.ss')).toBe(expected)
      })
    }
  })

  describe('format format: h:mm:ss.sss', () => {
    for (const [input, expected] of DURATION_FORMATTED_VALUES['h:mm:ss.sss']) {
      test(`"${input}" should be formatted to ${expected}`, () => {
        expect(formatDurationValue(input, 'h:mm:ss.sss')).toBe(expected)
      })
    }
  })

  describe('round value: d h', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['d h']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'd h')).toBe(expected)
      })
    }
  })

  describe('round value: d h:mm', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['d h:mm']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'd h:mm')).toBe(expected)
      })
    }
  })

  describe('round value: d h:mm:ss', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['d h:mm:ss']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'd h:mm:ss')).toBe(expected)
      })
    }
  })

  describe('round value: h:mm', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['h:mm']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'h:mm')).toBe(expected)
      })
    }
  })

  describe('round value: h:mm:ss', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['h:mm:ss']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'h:mm:ss')).toBe(expected)
      })
    }
  })

  describe('round value: h:mm:ss.s', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['h:mm:ss.s']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'h:mm:ss.s')).toBe(expected)
      })
    }
  })

  describe('round value: h:mm:ss.ss', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['h:mm:ss.ss']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'h:mm:ss.ss')).toBe(expected)
      })
    }
  })

  describe('round value: h:mm:ss.sss', () => {
    for (const [input, expected] of DURATION_ROUNDING_VALUES['h:mm:ss.sss']) {
      test(`"${input}" should be rounded to ${expected}`, () => {
        expect(roundDurationValueToFormat(input, 'h:mm:ss.sss')).toBe(expected)
      })
    }
  })
})
