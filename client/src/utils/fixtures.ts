import { CodeSystemsReponse } from '../api/schemas/codeSystemsReponse';
import { DbConfigurationCustomCode } from '../api/schemas/dbConfigurationCustomCode';
import { DbTotalConditionCodeCount } from '../api/schemas/dbTotalConditionCodeCount';
import { GetConfigurationResponse } from '../api/schemas/getConfigurationResponse';
import { GetConfigurationResponseVersion } from '../api/schemas/getConfigurationResponseVersion';

export const MOCK_CONFIG_ID = 'd8cf3930-a7c2-4761-9ba9-ce72ff9191c8';
export const MOCK_CONFIG_DRAFT_ID = '2d88054b-dd06-42de-8ae5-5a537889f4f8';

const mockCustomCodes: DbConfigurationCustomCode[] = [
  {
    code: 'custom-code1',
    name: 'test-custom-code1',
    system_key: 'icd10',
  },
];

const mockVersions: GetConfigurationResponseVersion[] = [
  {
    id: MOCK_CONFIG_ID,
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

export const mockCodeSystems: CodeSystemsReponse[] = [
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

export const mockCodeSets: DbTotalConditionCodeCount[] = [
  { condition_id: 'covid-1', display_name: 'COVID-19', total_codes: 12 },
  { condition_id: 'chlamydia-1', display_name: 'Chlamydia', total_codes: 8 },
  { condition_id: 'gonorrhea-1', display_name: 'Gonorrhea', total_codes: 5 },
];

export const baseMockConfig: GetConfigurationResponse = {
  id: MOCK_CONFIG_ID,
  condition_id: 'covid-19',
  draft_id: MOCK_CONFIG_DRAFT_ID,
  is_draft: true,
  display_name: 'COVID-19',
  status: 'draft',
  code_sets: mockCodeSets,
  custom_codes: {
    codes: mockCustomCodes,
    code_systems: {
      icd10: {
        key: 'icd10',
        id: '1cbe0833-7571-47b6-9374-48a3d60b2e43',
        display_name: 'ICD-10',
        oid: '2.16.840.1.113883.6.90',
      },
    },
  },
  section_processing: [
    {
      name: 'Encounters Section',
      code: 'some code',
      narrative: 'retain',
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
  rsg_codes: [],
  active_configuration_id: null,
  latest_version: 2,
  condition_canonical_url:
    'https://tes.tools.aimsplatform.org/api/fhir/ValueSet/123',
  locked_by: null,
  is_locked: false,
};

export const mockMutate = (response: unknown) =>
  vi.fn().mockImplementation(
    (
      _: { data: { condition_id: string } },
      options: {
        onSuccess?: (resp: unknown) => void;
        onError?: (e: unknown) => void;
      } = {}
    ) => {
      if (options.onSuccess) {
        options.onSuccess({ data: response });
      }
      return Promise.resolve({ data: response });
    }
  );
