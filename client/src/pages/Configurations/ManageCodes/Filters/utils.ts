export type ParamValue =
  string | number | boolean | (string | number | boolean)[] | null | undefined;

export function filterParamSerializer(params: Record<string, ParamValue>) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (Array.isArray(value)) {
      value.forEach((v) => searchParams.append(key, String(v)));
    } else if (value !== null && value !== undefined) {
      searchParams.append(key, String(value));
    }
  }

  return searchParams.toString();
}
