import { getClient } from '../client'
import { faker } from '@faker-js/faker'
import {Database} from "./database";
import {User} from "./user";
import {Table} from "./table";

export class Field {
    constructor(
        public id: number,
        public name: string,
        public type: string,
        public table:Table,
        public fieldSettings: any
    ) {
    }

    get primary(): boolean {
        return this.fieldSettings.primary;
    }
}

export async function createField(user: User, fieldName: string, type: string, fieldSettings: any, table: Table): Promise<Field> {
    const response: any = await getClient(user).post(`database/fields/table/${table.id}/`, {
        name: fieldName,
        type: type,
        ...fieldSettings
    })
    return new Field(
        response.data.id,
        response.data.name,
        response.data.type,
        table,
        response.data
    )
}

export async function updateField(user: User, fieldName: string, type: string, fieldSettings: any, field: Field): Promise<Field> {
    const response: any = await getClient(user).patch(`database/fields/${field.id}/`, {
        name: fieldName,
        type: type,
        ...fieldSettings
    })
    return new Field(
        response.data.id,
        response.data.name,
        response.data.type,
        field.table,
        response.data
    )
}

export async function deleteField(user: User, field: Field): Promise<void> {
    await getClient(user).delete(`database/fields/${field.id}/`)
}

export async function getFieldsForTable(user: User, table: Table): Promise<Field[]> {
    const response: any = await getClient(user).get(`database/fields/table/${table.id}/`)
    return response.data.map((f) => {
        return new Field(
            f.id,
            f.name,
            f.type,
            table,
            f
        )
    })
}

export async function deleteAllNonPrimaryFieldsFromTable(user: User, table: Table): Promise<void> {
    (await getFieldsForTable(user, table)).filter((f) => !f.primary).forEach((f) => deleteField(user, f))
}
