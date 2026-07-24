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
  GetConditionResponse,
  GetConditionsResponse,
  HTTPValidationError
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
 * Fetches a summary of all available conditions from the database and returns them as a list.
 *
 * Args:
 *     db (AsyncDatabaseConnection): Database connection.
 *
 * Returns:
 *     list[GetConditionsResponse]: List of all condition summaries.
 * @summary Get Conditions
 */
export const getConditions = (
     options?: AxiosRequestConfig
 ): Promise<AxiosResponse<GetConditionsResponse[]>> => {


    return axios.default.get(
      `/api/v1/conditions/`,options
    );
  }




export const getGetConditionsQueryKey = () => {
    return [
    `/api/v1/conditions/`
    ] as const;
    }


export const getGetConditionsQueryOptions = <TData = Awaited<ReturnType<typeof getConditions>>, TError = AxiosError<unknown>>( options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetConditionsQueryKey();



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getConditions>>> = ({ signal }) => getConditions({ signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetConditionsQueryResult = NonNullable<Awaited<ReturnType<typeof getConditions>>>
export type GetConditionsQueryError = AxiosError<unknown>


export function useGetConditions<TData = Awaited<ReturnType<typeof getConditions>>, TError = AxiosError<unknown>>(
  options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getConditions>>,
          TError,
          Awaited<ReturnType<typeof getConditions>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetConditions<TData = Awaited<ReturnType<typeof getConditions>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getConditions>>,
          TError,
          Awaited<ReturnType<typeof getConditions>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetConditions<TData = Awaited<ReturnType<typeof getConditions>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Conditions
 */

export function useGetConditions<TData = Awaited<ReturnType<typeof getConditions>>, TError = AxiosError<unknown>>(
  options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getConditions>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetConditionsQueryOptions(options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}






/**
 * Returns information about a given condition.
 *
 * Args:
 *     condition_id (UUID): ID of the condition
 *     db (AsyncDatabaseConnection): Database connection.
 *
 * Raises:
 *     HTTPException: 404 if no condition is found
 *
 * Returns:
 *     GetCondition: Info about the condition
 * @summary Get Condition
 */
export const getCondition = (
    conditionId: string, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<GetConditionResponse>> => {


    return axios.default.get(
      `/api/v1/conditions/${conditionId}`,options
    );
  }




export const getGetConditionQueryKey = (conditionId: string,) => {
    return [
    `/api/v1/conditions/${conditionId}`
    ] as const;
    }


export const getGetConditionQueryOptions = <TData = Awaited<ReturnType<typeof getCondition>>, TError = AxiosError<HTTPValidationError>>(conditionId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetConditionQueryKey(conditionId);



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getCondition>>> = ({ signal }) => getCondition(conditionId, { signal, ...axiosOptions });





   return  { queryKey, queryFn, enabled: conditionId !== null && conditionId !== undefined, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetConditionQueryResult = NonNullable<Awaited<ReturnType<typeof getCondition>>>
export type GetConditionQueryError = AxiosError<HTTPValidationError>


export function useGetCondition<TData = Awaited<ReturnType<typeof getCondition>>, TError = AxiosError<HTTPValidationError>>(
 conditionId: string, options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCondition>>,
          TError,
          Awaited<ReturnType<typeof getCondition>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCondition<TData = Awaited<ReturnType<typeof getCondition>>, TError = AxiosError<HTTPValidationError>>(
 conditionId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCondition>>,
          TError,
          Awaited<ReturnType<typeof getCondition>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCondition<TData = Awaited<ReturnType<typeof getCondition>>, TError = AxiosError<HTTPValidationError>>(
 conditionId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Condition
 */

export function useGetCondition<TData = Awaited<ReturnType<typeof getCondition>>, TError = AxiosError<HTTPValidationError>>(
 conditionId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCondition>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetConditionQueryOptions(conditionId,options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}
