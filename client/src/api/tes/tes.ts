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
  GetTesUpdateDiffParams,
  HTTPValidationError,
  TesDiffResponse,
  TesResponse
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
 * Returns a list of all TES updates, ordered from newest to oldest.
 *
 * Args:
 *     db (AsyncDatabaseConnection): Database connection.
 *
 * Returns:
 *     TesResponse: A bundle with a list of TesUpdates, including
 *         - The version
 *         - The when it was created
 * @summary Get Tes Updates
 */
export const getTesUpdates = (
     options?: AxiosRequestConfig
 ): Promise<AxiosResponse<TesResponse>> => {


    return axios.default.get(
      `/api/v1/tes/diff-details`,options
    );
  }




export const getGetTesUpdatesQueryKey = () => {
    return [
    `/api/v1/tes/diff-details`
    ] as const;
    }


export const getGetTesUpdatesQueryOptions = <TData = Awaited<ReturnType<typeof getTesUpdates>>, TError = AxiosError<unknown>>( options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetTesUpdatesQueryKey();



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getTesUpdates>>> = ({ signal }) => getTesUpdates({ signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetTesUpdatesQueryResult = NonNullable<Awaited<ReturnType<typeof getTesUpdates>>>
export type GetTesUpdatesQueryError = AxiosError<unknown>


export function useGetTesUpdates<TData = Awaited<ReturnType<typeof getTesUpdates>>, TError = AxiosError<unknown>>(
  options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getTesUpdates>>,
          TError,
          Awaited<ReturnType<typeof getTesUpdates>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetTesUpdates<TData = Awaited<ReturnType<typeof getTesUpdates>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getTesUpdates>>,
          TError,
          Awaited<ReturnType<typeof getTesUpdates>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetTesUpdates<TData = Awaited<ReturnType<typeof getTesUpdates>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Tes Updates
 */

export function useGetTesUpdates<TData = Awaited<ReturnType<typeof getTesUpdates>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdates>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetTesUpdatesQueryOptions(options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}






/**
 * Returns a list of all TES updates, ordered from newest to oldest.
 *
 * Args:
 *     cur_version: Version to compare against.
 *     prev_version: Version to compare against.
 *     db (AsyncDatabaseConnection): Database connection.
 *
 * Returns:
 *     TesResponse: A bundle with a list of TesUpdates, including
 *         - The version
 *         - The when it was created
 * @summary Get Tes Diff Details
 */
export const getTesUpdateDiff = (
    params: GetTesUpdateDiffParams, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<TesDiffResponse[]>> => {


    return axios.default.get(
      `/api/v1/tes/`,{
    ...options,
        params: {...params, ...options?.params},}
    );
  }




export const getGetTesUpdateDiffQueryKey = (params?: GetTesUpdateDiffParams,) => {
    return [
    `/api/v1/tes/`, ...(params ? [params] : [])
    ] as const;
    }


export const getGetTesUpdateDiffQueryOptions = <TData = Awaited<ReturnType<typeof getTesUpdateDiff>>, TError = AxiosError<HTTPValidationError>>(params: GetTesUpdateDiffParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetTesUpdateDiffQueryKey(params);



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getTesUpdateDiff>>> = ({ signal }) => getTesUpdateDiff(params, { signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetTesUpdateDiffQueryResult = NonNullable<Awaited<ReturnType<typeof getTesUpdateDiff>>>
export type GetTesUpdateDiffQueryError = AxiosError<HTTPValidationError>


export function useGetTesUpdateDiff<TData = Awaited<ReturnType<typeof getTesUpdateDiff>>, TError = AxiosError<HTTPValidationError>>(
 params: GetTesUpdateDiffParams, options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getTesUpdateDiff>>,
          TError,
          Awaited<ReturnType<typeof getTesUpdateDiff>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetTesUpdateDiff<TData = Awaited<ReturnType<typeof getTesUpdateDiff>>, TError = AxiosError<HTTPValidationError>>(
 params: GetTesUpdateDiffParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getTesUpdateDiff>>,
          TError,
          Awaited<ReturnType<typeof getTesUpdateDiff>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetTesUpdateDiff<TData = Awaited<ReturnType<typeof getTesUpdateDiff>>, TError = AxiosError<HTTPValidationError>>(
 params: GetTesUpdateDiffParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Tes Diff Details
 */

export function useGetTesUpdateDiff<TData = Awaited<ReturnType<typeof getTesUpdateDiff>>, TError = AxiosError<HTTPValidationError>>(
 params: GetTesUpdateDiffParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getTesUpdateDiff>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetTesUpdateDiffQueryOptions(params,options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}
