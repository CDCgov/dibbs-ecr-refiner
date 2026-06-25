export const EXAMPLE_LOINC_CODE = '99999A';
export const EXAMPLE_SNOMED_CODE = '1115565';
export const EXAMPLE_CVX_CODE = '143';
export const EXAMPLE_OTHER_CODE_SUFFIX = '1534';
export const EXAMPLE_OTHER_CODE = EXAMPLE_CVX_CODE + EXAMPLE_OTHER_CODE_SUFFIX; // used to test prefix matching

export const CSV_DOWNLOAD_TEMPLATE = `code,code_system,display_name
${EXAMPLE_SNOMED_CODE},SNOMED,SNOMED Example
${EXAMPLE_OTHER_CODE},Other,Other Example
6789,ICD-10,ICD-10 Example
${EXAMPLE_LOINC_CODE},LOINC,LOINC Example
${EXAMPLE_CVX_CODE},CVX,CVX Example
198440,RxNorm,RxNorm Example
`;
