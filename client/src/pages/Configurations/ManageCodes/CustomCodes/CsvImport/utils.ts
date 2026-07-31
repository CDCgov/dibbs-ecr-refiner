import { DbCodeSystem } from '../../../../../api/schemas/dbCodeSystem';

export function buildCsvDownloadTemplate(systemsSupported: DbCodeSystem[]) {
  const headers = 'code,code_system,display_name';

  let content = headers + '\n';
  systemsSupported.forEach((s) => {
    const exampleCode = `1111111-${s.key}`;

    const currentRow =
      exampleCode + ',' + s.display_name + ',' + `${s.display_name} Example`;
    content += currentRow + '\n';
  });

  return content;
}
