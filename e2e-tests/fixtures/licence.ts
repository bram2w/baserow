import { getClient } from '../client'
import { getStaffUser, User } from "./user";


export type License = {
    id?: number,
    license: string,
    alreadyExistedAtStart:boolean
}

const ENTERPRISE_LICENSE = "eyJ2ZXJzaW9uIjogMSwgImlkIjogIjUzODczYmVkLWJlNTQtNDEwZS04N2" +
    "EzLTE2OTM2ODY2YjBiNiIsICJ2YWxpZF9mcm9tIjogIjIwMjItMTAtMDFUMDA6MDA6MDAiLCAidmFsaWR" +
    "fdGhyb3VnaCI6ICIyMDY5LTA4LTA5VDIzOjU5OjU5IiwgInByb2R1Y3RfY29kZSI6ICJlbnRlcnByaXNl" +
    "IiwgInNlYXRzIjogMSwgImlzc3VlZF9vbiI6ICIyMDIyLTEwLTI2VDE0OjQ4OjU0LjI1OTQyMyIsICJpc" +
    "3N1ZWRfdG9fZW1haWwiOiAidGVzdEB0ZXN0LmNvbSIsICJpc3N1ZWRfdG9fbmFtZSI6ICJ0ZXN0QHRlc3" +
    "QuY29tIiwgImluc3RhbmNlX2lkIjogIjEifQ==.B7aPXR0R4Fxr28AL7B5oopa2Yiz_MmEBZGdzSEHHLt" +
    "4wECpnzjd_SF440KNLEZYA6WL1rhNkZ5znbjYIp6KdCqLdcm1XqNYOIKQvNTOtl9tUAYj_Qvhq1jhqSja" +
    "-n3HFBjIh9Ve7a6T1PuaPLF1DoxSRGFZFXliMeJRBSzfTsiHiO22xRQ4GwafscYfUIWvIJJHGHtYEd9rk" +
    "0tG6mfGEaQGB4e6KOsN-zw-bgLDBOKmKTGrVOkZnaGHBVVhUdpBn25r3CFWqHIApzUCo81zAA96fECHPl" +
    "x_fBHhvIJXLsN5i3LdeJlwysg5SBO15Vt-tsdPmdcsec-fOzik-k3ib0A==\n"

export { ENTERPRISE_LICENSE }

export async function createLicense(key: string, user?: User): Promise<any> {
    /**
     * Responsible for creating a new license. If a `user` isn't provided,
     * we'll use the base e2e staff user.
     */
    user = user === undefined ? await getStaffUser() : user
    try {
        const response: any = await getClient(user).post('licenses/', {
            license: key
        })
        return {
            id: response.data.id,
            alreadyExistedAtStart: false
        }
    } catch (e){
        if(e?.response?.data?.error === 'ERROR_LICENSE_ALREADY_EXISTS'){
            return {
                alreadyExistedAtStart: true
            }
        } else {
            throw e
        }
    }
}

export async function deleteLicense(license: License, user?: User): Promise<any> {
    /**
     * Responsible for destroying an existing license. If a `user` isn't provided,
     * we'll use the base e2e staff user.
     */
    if (!process.env.CI && !license.alreadyExistedAtStart) {
        user = user === undefined ? await getStaffUser() : user
        await getClient(user).delete(`licenses/${license.id}/`)
    }
}
