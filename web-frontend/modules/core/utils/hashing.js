import crypto from 'crypto'

export function generateHash(value) {
  return crypto.createHash('sha256').update(value.toString()).digest('hex')
}
