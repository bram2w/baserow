import { getClient } from '../client'
import {User} from "./user";

export class Workspace{
    constructor(
        public id: number,
        public name: string,
    ) {
    }
}

export async function getUsersFirstWorkspace(user: User): Promise<Workspace> {
    const response: any = await getClient(user).get('workspaces/', {
    })
    let firstWorkspaceData = response.data[0];
    return new Workspace(firstWorkspaceData.id,
        firstWorkspaceData.name)
}

