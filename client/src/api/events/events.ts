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
  CustomCodeUploadEventResponse,
  EventsResponse,
  GetEventsExportApiV1EventsExportGetParams,
  GetEventsParams,
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
 * Returns a list of all events for a jurisdiction, ordered from newest to oldest.
 *
 * Args:
 *     user (DbUser): The user making the request.
 *     db (AsyncDatabaseConnection): Database connection.
 *     logger (Logger): Standard logger.
 *     page (int): page of events to return to the client.
 *     canonical_url (str | None): An optional filter on the condition.
 *
 * Returns:
 *     EventResponse: A bundle with
 *         - Total page count
 *         - The list of AuditEvents relevant for the (optional) filter
 *         - The list of condition information with potentially filter-able data
 * @summary Get Events
 */
export const getEvents = (
    params?: GetEventsParams, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<EventsResponse>> => {


    return axios.default.get(
      `/api/v1/events/`,{
    ...options,
        params: {...params, ...options?.params},}
    );
  }




export const getGetEventsQueryKey = (params?: GetEventsParams,) => {
    return [
    `/api/v1/events/`, ...(params ? [params] : [])
    ] as const;
    }


export const getGetEventsQueryOptions = <TData = Awaited<ReturnType<typeof getEvents>>, TError = AxiosError<HTTPValidationError>>(params?: GetEventsParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetEventsQueryKey(params);



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getEvents>>> = ({ signal }) => getEvents(params, { signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetEventsQueryResult = NonNullable<Awaited<ReturnType<typeof getEvents>>>
export type GetEventsQueryError = AxiosError<HTTPValidationError>


export function useGetEvents<TData = Awaited<ReturnType<typeof getEvents>>, TError = AxiosError<HTTPValidationError>>(
 params: undefined |  GetEventsParams, options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getEvents>>,
          TError,
          Awaited<ReturnType<typeof getEvents>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetEvents<TData = Awaited<ReturnType<typeof getEvents>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getEvents>>,
          TError,
          Awaited<ReturnType<typeof getEvents>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetEvents<TData = Awaited<ReturnType<typeof getEvents>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Events
 */

export function useGetEvents<TData = Awaited<ReturnType<typeof getEvents>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetEventsQueryOptions(params,options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}






/**
 * Returns a list of all custom code upload events associated with a parent event ID.
 *
 * Args:
 *     event_id (UUID): The parent event
 *     user (DbUser): The logged in user
 *     db (AsyncDatabaseConnection): The database connection
 *
 * Raises:
 *     HTTPException: 404 if event with requested ID is not found or does not belong to user's jurisdiction
 * @summary Get Custom Code Upload Events
 */
export const getCustomCodeUploadEvents = (
    eventId: string, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<CustomCodeUploadEventResponse[]>> => {


    return axios.default.get(
      `/api/v1/events/${eventId}/custom-code-uploads`,options
    );
  }




export const getGetCustomCodeUploadEventsQueryKey = (eventId: string,) => {
    return [
    `/api/v1/events/${eventId}/custom-code-uploads`
    ] as const;
    }


export const getGetCustomCodeUploadEventsQueryOptions = <TData = Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError = AxiosError<HTTPValidationError>>(eventId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetCustomCodeUploadEventsQueryKey(eventId);



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>> = ({ signal }) => getCustomCodeUploadEvents(eventId, { signal, ...axiosOptions });





   return  { queryKey, queryFn, enabled: eventId !== null && eventId !== undefined, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetCustomCodeUploadEventsQueryResult = NonNullable<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>>
export type GetCustomCodeUploadEventsQueryError = AxiosError<HTTPValidationError>


export function useGetCustomCodeUploadEvents<TData = Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError = AxiosError<HTTPValidationError>>(
 eventId: string, options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCustomCodeUploadEvents>>,
          TError,
          Awaited<ReturnType<typeof getCustomCodeUploadEvents>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCustomCodeUploadEvents<TData = Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError = AxiosError<HTTPValidationError>>(
 eventId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getCustomCodeUploadEvents>>,
          TError,
          Awaited<ReturnType<typeof getCustomCodeUploadEvents>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetCustomCodeUploadEvents<TData = Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError = AxiosError<HTTPValidationError>>(
 eventId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Custom Code Upload Events
 */

export function useGetCustomCodeUploadEvents<TData = Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError = AxiosError<HTTPValidationError>>(
 eventId: string, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getCustomCodeUploadEvents>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetCustomCodeUploadEventsQueryOptions(eventId,options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}






/**
 * Generate a CSV export of all events within a jurisdiction.
 *
 * Args:
 *     timezone (str): The user's timezone as a string
 *     user (DbUser): The logged-in user
 *     db (AsyncDatabaseConnection): The database connection
 *     canonical_url (str | None): An optional canonical URL to filter the export by condition
 *
 * Returns:
 *     Response: The generated CSV file
 * @summary Get Events Export
 */
export const getEventsExportApiV1EventsExportGet = (
    params?: GetEventsExportApiV1EventsExportGetParams, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<void>> => {


    return axios.default.get(
      `/api/v1/events/export`,{
    ...options,
        params: {...params, ...options?.params},}
    );
  }




export const getGetEventsExportApiV1EventsExportGetQueryKey = (params?: GetEventsExportApiV1EventsExportGetParams,) => {
    return [
    `/api/v1/events/export`, ...(params ? [params] : [])
    ] as const;
    }


export const getGetEventsExportApiV1EventsExportGetQueryOptions = <TData = Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError = AxiosError<HTTPValidationError>>(params?: GetEventsExportApiV1EventsExportGetParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData>>, axios?: AxiosRequestConfig}
) => {

const {query: queryOptions, axios: axiosOptions} = options ?? {};

  const queryKey =  queryOptions?.queryKey ?? getGetEventsExportApiV1EventsExportGetQueryKey(params);



    const queryFn: QueryFunction<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>> = ({ signal }) => getEventsExportApiV1EventsExportGet(params, { signal, ...axiosOptions });





   return  { queryKey, queryFn, ...queryOptions} as UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData> & { queryKey: DataTag<QueryKey, TData, TError> }
}

export type GetEventsExportApiV1EventsExportGetQueryResult = NonNullable<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>>
export type GetEventsExportApiV1EventsExportGetQueryError = AxiosError<HTTPValidationError>


export function useGetEventsExportApiV1EventsExportGet<TData = Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError = AxiosError<HTTPValidationError>>(
 params: undefined |  GetEventsExportApiV1EventsExportGetParams, options: { query:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData>> & Pick<
        DefinedInitialDataOptions<
          Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>,
          TError,
          Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  DefinedUseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetEventsExportApiV1EventsExportGet<TData = Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsExportApiV1EventsExportGetParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData>> & Pick<
        UndefinedInitialDataOptions<
          Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>,
          TError,
          Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>
        > , 'initialData'
      >, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
export function useGetEventsExportApiV1EventsExportGet<TData = Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsExportApiV1EventsExportGetParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
  ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> }
/**
 * @summary Get Events Export
 */

export function useGetEventsExportApiV1EventsExportGet<TData = Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError = AxiosError<HTTPValidationError>>(
 params?: GetEventsExportApiV1EventsExportGetParams, options?: { query?:Partial<UseQueryOptions<Awaited<ReturnType<typeof getEventsExportApiV1EventsExportGet>>, TError, TData>>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient
 ):  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> } {

  const queryOptions = getGetEventsExportApiV1EventsExportGetQueryOptions(params,options)

  const query = useQuery(queryOptions, queryClient) as  UseQueryResult<TData, TError> & { queryKey: DataTag<QueryKey, TData, TError> };

  return withQueryKey(query, queryOptions.queryKey);
}
