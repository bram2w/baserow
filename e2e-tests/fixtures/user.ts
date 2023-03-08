import { getClient } from '../client'
import { faker } from '@faker-js/faker'

export type User = {
  name: string,
  email: string,
  password: string,
  language: string,
  accessToken: string,
  refreshToken: string,
}

export async function createUser(): Promise<User> {
  const password = faker.internet.password()
  const response: any = await getClient().post('user/', {
    name: faker.name.fullName(),
    email: faker.internet.email(),
    password,
    language: 'en',
    authenticate: true,
  })
  return {
    name: response.data.user.first_name,
    email: response.data.user.username,
    password,
    language: response.data.user.language,
    accessToken: response.data.access_token,
    refreshToken: response.data.refresh_token,
  }
}

export async function deleteUser(user: User): Promise<any> {
  await getClient(user).post('user/schedule-account-deletion/')
}