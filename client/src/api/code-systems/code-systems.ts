import {
  useQuery
} from '@tanstack/react-query';
import type {
  DataTag,
  DefinedInitialDataOptions,
  DefinedUseQueryResult,
  QueryClient,
  QueryFunction,
  QueryKey,
  UndefinedInitialDataOptions,
  UseQueryOptions,
  UseQueryResult
} from '@tanstack/react-query';

import * as axios from 'axios';
import type {
  AxiosError,
  AxiosRequestConfig,
  AxiosResponse
} from 'axios';

import type {
  CodeSystemsReponse
} from '../schemas';





const withQueryKey = <T extends object, K>(query: T, queryKey: K): T & { queryKey: K } => {
  const result = { queryKey } as T & { queryKey: K };
  for (const key of Object.keys(query)) {
    // The explicit queryKey always wins, matching the previous
    // `{ ...query, queryKey }` spread where it was set last.
    if (key === 'queryKey') continue;
    Object.defineProperty(result, key, {
      enumerable: true,
      configurable: true,
      get: () => (query as Record<string, unknown>)[key],
    });
  }
  return result;
};

/**
 * Returns a list of supported code systems.
 *
 * Returns:
 *     List of code system.
 * @summary Get Code Systems
 */
export const getCodeSystems = (
     options?: AxiosRequestConfig
 ): Promise<AxiosResponse<CodeSystemsReponse[]>> => {


    return axios.default.get(
      `/api/v1/code-systems/`,options
    );
  }




export const getGetCodeSystemsQueryKey = () => {
    return [
    `/api/v1/code-systems/`
    ] as const;
    }


export const getGetCodeSystemsQueryOptions = <TData = Awaited<ReturnType<typeof getCodeSystems>>, TError = AxiosError<unknown>>( options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetCodeSystemsQueryKey();



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getCodeSystems>>> = ({ signal }) => getCodeSystems({ signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetCodeSystemsQueryResult = NonNullable<Awaited<ReturnType<typeof getCodeSystems>>>
export type GetCodeSystemsQueryError = AxiosError<unknown>


export function useGetCodeSystems<TData = Awaited<ReturnType<typeof getCodeSystems>>, TError = AxiosError<unknown>>(
  options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCodeSystems>>,
          TError,
          Awaited<ReturnType<typeof getCodeSystems>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCodeSystems<TData = Awaited<ReturnType<typeof getCodeSystems>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCodeSystems>>,
          TError,
          Awaited<ReturnType<typeof getCodeSystems>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCodeSystems<TData = Awaited<ReturnType<typeof getCodeSystems>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Code Systems
 */

export function useGetCodeSystems<TData = Awaited<ReturnType<typeof getCodeSystems>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCodeSystems>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetCodeSystemsQueryOptions(options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}
