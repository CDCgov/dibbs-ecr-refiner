import { DbCodeSystem } from '../../../../../api/schemas/dbCodeSystem';

export function buildCsvDownloadTemplate(systemsSupported: DbCodeSystem[]) {
  const headers = 'code,code_system,display_name';

  let content = headers + '\n';
  systemsSupported.forEach((s) => {
    const randomLengthAtLeastThree = 3 + Math.floor(Math.random() * 10);
    const randomCode = Array.from({ length: randomLengthAtLeastThree }, () =>
      Math.floor(Math.random() * 10)
    ).join('');

    const currentRow =
      randomCode + ',' + s.key + ',' + `${s.display_name} Example`;
    content += currentRow + '\n';
  });

  return content;
}
