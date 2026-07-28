import { DbCodeSystem, DbTotalConditionCodeCount } from '../../../api/schemas';
import { DbConfigurationCustomCode } from '../../../api/schemas/dbConfigurationCustomCode';

export const MOCK_CONFIG_DRAFT_ID = 'b8f96556-2567-48c1-9d1a-cf3e202e5fdb';
export const mockCustomCodes: DbConfigurationCustomCode[] = [
  {
    code: 'custom-code1',
    name: 'test-custom-code1',
    system_key: 'icd10',
  },
];

export const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
  { condition_id: 'chlamydia-1', display_name: 'Chlamydia', total_codes: 8 },
  { condition_id: 'gonorrhea-1', display_name: 'Gonorrhea', total_codes: 5 },
];

export const mockCodeSystems: DbCodeSystem[] = [
  {
    id: '157a00b0-62e6-48c8-b822-475c5d855f3f',
    key: 'snomed',
    display_name: 'SNOMED',
    oid: '2.16.840.1.113883.6.96',
  },
  {
    id: 'bd5ad8fd-f94c-4fcf-97ee-5b63c2e7a42b',
    oid: '2.16.840.1.113883.6.1',
    key: 'loinc',
    display_name: 'LOINC',
  },
  {
    id: '375d4fd5-81f8-4b9e-abd9-979c7987691f',
    oid: '2.16.840.1.113883.6.90',
    key: 'icd10',
    display_name: 'ICD-10',
  },
  {
    id: 'c645801a-26f2-495c-b07f-e9be5ac26275',
    oid: '2.16.840.1.113883.6.88',
    key: 'rxnorm',
    display_name: 'RxNorm',
  },
  {
    id: '4306c91c-a8e2-4f4b-b673-0da9a6432b38',
    oid: '2.16.840.1.113883.12.292',
    key: 'cvx',
    display_name: 'CVX',
  },
  {
    id: 'f65063a3-6836-41ce-8ab8-253994907faa',
    oid: 'Other',
    key: 'other',
    display_name: 'Other',
  },
];
