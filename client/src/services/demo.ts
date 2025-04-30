import { useQuery, useQueryClient } from '@tanstack/react-query';

async function upload(): Promise<string> {
  const resp = await fetch('/api/demo/upload');
  return resp.text();
}

const uploadKey = 'upload';

export function useDemoUpload() {
  const queryClient = useQueryClient();

  async function resetData() {
    await queryClient.resetQueries({ queryKey: [uploadKey], exact: true });
  }

  return {
    ...useQuery({
      queryKey: [uploadKey],
      queryFn: upload,
      enabled: false,
      initialData: '',
    }),
    resetData,
  };
}
