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
  HTTPValidationError,
  UpdateUserNotificationsRequest,
  UserResponse
} from '../schemas';





/**
 * Updates notification acknowledgement state for the current user.
 * @summary Update User Notifications
 */
export const updateUserNotifications = (
    updateUserNotificationsRequest: UpdateUserNotificationsRequest, options?: AxiosRequestConfig
 ): Promise<AxiosResponse<UserResponse>> => {


    return axios.default.patch(
      `/api/v1/notifications`,
      updateUserNotificationsRequest,options
    );
  }




export const getUpdateUserNotificationsMutationKey = () => ['updateUserNotifications'] as const;

export const getUpdateUserNotificationsMutationOptions = <TError = AxiosError<HTTPValidationError>,
    TContext = unknown>(options?: { mutation?:UseMutationOptions<Awaited<ReturnType<typeof updateUserNotifications>>, TError,UpdateUserNotificationsMutationVariables, TContext>, axios?: AxiosRequestConfig}
): UseMutationOptions<Awaited<ReturnType<typeof updateUserNotifications>>, TError,UpdateUserNotificationsMutationVariables, TContext> => {

const mutationKey = getUpdateUserNotificationsMutationKey();
const {mutation: mutationOptions, axios: axiosOptions} = options ?
      options.mutation && 'mutationKey' in options.mutation && options.mutation.mutationKey ?
      options
      : {...options, mutation: {...options.mutation, mutationKey}}
      : {mutation: { mutationKey, }, axios: undefined};




      const mutationFn: MutationFunction<Awaited<ReturnType<typeof updateUserNotifications>>, UpdateUserNotificationsMutationVariables> = (props) => {
          const {data} = props ?? {};

          return  updateUserNotifications(data,axiosOptions)
        }






  return  { mutationFn, ...mutationOptions }}

    export type UpdateUserNotificationsMutationResult = NonNullable<Awaited<ReturnType<typeof updateUserNotifications>>>
    export type UpdateUserNotificationsMutationBody = UpdateUserNotificationsRequest
    export type UpdateUserNotificationsMutationError = AxiosError<HTTPValidationError>
    export type UpdateUserNotificationsMutationVariables = {data: UpdateUserNotificationsRequest}

    /**
 * @summary Update User Notifications
 */
export const useUpdateUserNotifications = <TError = AxiosError<HTTPValidationError>,
    TContext = unknown>(options?: { mutation?:UseMutationOptions<Awaited<ReturnType<typeof updateUserNotifications>>, TError,UpdateUserNotificationsMutationVariables, TContext>, axios?: AxiosRequestConfig}
 , queryClient?: QueryClient): UseMutationResult<
        Awaited<ReturnType<typeof updateUserNotifications>>,
        TError,
        UpdateUserNotificationsMutationVariables,
        TContext
      > => {
      return useMutation(getUpdateUserNotificationsMutationOptions(options), queryClient);
    }
