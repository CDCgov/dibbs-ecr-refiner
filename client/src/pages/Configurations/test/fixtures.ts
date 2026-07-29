import {
  CustomCodeResponse,
  DbCodeSystem,
  DbTotalConditionCodeCount,
  GetConfigurationResponse,
  GetConfigurationResponseVersion,
} from '../../../api/schemas';

export const MOCK_CONFIG_DRAFT_ID = 'b8f96556-2567-48c1-9d1a-cf3e202e5fdb';

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

export const mockCustomCodes: CustomCodeResponse[] = [
  {
    id: '3c4ee804-dad5-42ba-b786-4dd752779197',
    code: 'custom-code1',
    display: 'test-custom-code1',
    system_id: mockCodeSystems.find((cs) => cs.display_name === 'ICD-10')!.id,
    system_name: 'ICD-10',
  },
];

const MOCK_SNOMED_DB_ID = '37a4a3f9-6148-41aa-bf45-f1aed2d4caa9';

const mockVersions: GetConfigurationResponseVersion[] = [
  {
    id: 'config-id',
    version: 2,
    status: 'draft',
    condition_canonical_url:
      'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
    created_at: '2025-12-18 18:01:40.660826+00',
    last_activated_at: '',
    created_by: 'mock-user-1',
    last_activated_by: null,
  },
  {
    id: 'prev-id',
    version: 1,
    status: 'active',
    condition_canonical_url:
      'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
    created_at: '2025-12-09 18:01:40.660826+00',
    last_activated_at: '2025-12-09 9:01:40.660826+00',
    created_by: 'mock-user-1',
    last_activated_by: 'mock-user-2',
  },
];

export const baseMockConfig: GetConfigurationResponse = {
  id: MOCK_CONFIG_DRAFT_ID,
  condition_id: 'covid-19',
  draft_id: 'config-id',
  is_draft: true,
  display_name: 'COVID-19',
  status: 'draft',
  code_sets: mockCodeSets,
  rsg_codes: [
    {
      display: 'Coronavirus infection (disorder)',
      code: '186747009',
      version: '6.0.0',
      system_id: MOCK_SNOMED_DB_ID,
    },
    {
      display:
        'Disease caused by severe acute respiratory syndrome coronavirus 2 (disorder)',
      code: '840539006',
      version: '6.0.0',
      system_id: MOCK_SNOMED_DB_ID,
    },
    {
      display:
        'Death associated with disease caused by severe acute respiratory syndrome coronavirus 2 (event)',
      code: '1001411000124108',
      version: '6.0.0',
      system_id: MOCK_SNOMED_DB_ID,
    },
  ],
  custom_codes: mockCustomCodes,
  section_processing: [
    {
      name: 'Encounters Section',
      code: 'some code',
      narrative: 'remove',
      include: true,
      action: 'refine',
      versions: ['1.1'],
      section_type: 'standard',
    },
  ],
  included_conditions: [],
  all_versions: mockVersions,
  version: 2,
  active_version: null,
  active_configuration_id: null,
  latest_version: 2,
  condition_canonical_url:
    'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
  locked_by: null,
  is_locked: false,
};
