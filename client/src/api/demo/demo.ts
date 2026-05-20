import {
  useMutation
} from '@tanstack/react-query';
import type {
  MutationFunction,
  QueryClient,
  UseMutationOptions,
  UseMutationResult
} from '@tanstack/react-query';

import * as axios from 'axios';
import type {
  AxiosError,
  AxiosRequestConfig,
  AxiosResponse
} from 'axios';

import type {
  BodyDiscoverConfigurations,
  DiscoveredConfigurationsResponse,
  HTTPValidationError
} from '../schemas';





/**
 * Detects reportable conditions found in `uploaded_file` and matches them with existing configurations.

Configurations are returned to the client.

Args:
    uploaded_file (UploadFile | None, optional): The eCR file package uploaded by the user.
    demo_zip_path (Path, optional): The path to the demo zip file.
    user (DbUser, optional): The logged in user.
    db (AsyncDatabaseConnection, optional): The database connection.
    logger (Logger, optional): The app logger.

Returns:
    DiscoveredConfigurationsResponse: Matching configurations, grouped by condition.
 * @summary Discover Configurations
 */
export const discoverConfigurations = (
    bodyDiscoverConfigurations?: BodyDiscoverConfigurations, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<DiscoveredConfigurationsResponse>> => {

    const formData = new FormData();
if(bodyDiscoverConfigurations?.uploaded_file !== undefined && bodyDiscoverConfigurations.uploaded_file !== null) {
 formData.append(`uploaded_file`, bodyDiscoverConfigurations.uploaded_file);
 }

    return axios.default.post(
      `/api/v1/simulator/discover-configurations`,
      formData,options
    );
  }



export const getDiscoverConfigurationsMutationOptions = <TError = AxiosError<HTTPValidationError>,
    TContext = unknown>(options?: { mutation?:UseMutationOptions<Awaited<ReturnType<typeof discoverConfigurations>>, TError,{data?: BodyDiscoverConfigurations}, TContext>, axios?: AxiosRequestConfig}
): UseMutationOptions<Awaited<ReturnType<typeof discoverConfigurations>>, TError,{data?: BodyDiscoverConfigurations}, TContext> => {

const mutationKey = ['discoverConfigurations'];
const {mutation: mutationOptions, axios: axiosOptions} = options ?
      options.mutation && 'mutationKey' in options.mutation && options.mutation.mutationKey ?
      options
      : {...options, mutation: {...options.mutation, mutationKey}}
      : {mutation: { mutationKey, }, axios: undefined};




      const mutationFn: MutationFunction<Awaited<ReturnType<typeof discoverConfigurations>>, {data?: BodyDiscoverConfigurations}> = (props) => {
          const {data} = props ?? {};

          return  discoverConfigurations(data,axiosOptions)
        }






  return  { mutationFn, ...mutationOptions }}

    export type DiscoverConfigurationsMutationResult = NonNullable<Awaited<ReturnType<typeof discoverConfigurations>>>
    export type DiscoverConfigurationsMutationBody = BodyDiscoverConfigurations | undefined
    export type DiscoverConfigurationsMutationError = AxiosError<HTTPValidationError>

    /**
 * @summary Discover Configurations
 */
export const useDiscoverConfigurations = <TError = AxiosError<HTTPValidationError>,
    TContext = unknown>(options?: { mutation?:UseMutationOptions<Awaited<ReturnType<typeof discoverConfigurations>>, TError,{data?: BodyDiscoverConfigurations}, TContext>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient): UseMutationResult<
        Awaited<ReturnType<typeof discoverConfigurations>>,
        TError,
        {data?: BodyDiscoverConfigurations},
        TContext
      > => {
      return useMutation(getDiscoverConfigurationsMutationOptions(options), queryClient);
    }
