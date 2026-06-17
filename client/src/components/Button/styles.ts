import classNames from 'classnames';
import { ButtonVariant } from '.';

const sharedStyles =
  'm-0 appearance-none cursor-pointer text-center rounded justify-center items-center gap-2 mr-2 px-5 py-3 font-bold leading-none no-underline inline-flex';

export const SECONDARY_BUTTON_STYLES = classNames(
  sharedStyles,
  'bg-white text-violet-warm-60 hover:text-violet-warm-70 hover:border-violet-warm-70 border-violet-warm-60 border-[2px]'
);

export const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary: classNames(
    sharedStyles,
    'bg-violet-warm-60 hover:bg-violet-warm-70 text-white border-0'
  ),
  secondary: SECONDARY_BUTTON_STYLES,
  tertiary: classNames(
    sharedStyles,
    'text-blue-cool-60 hover:underline hover:text-blue-cool-50'
  ),
  unstyled: '',
};

export const DISABLED_STYLES =
  'bg-zinc-200 text-gray-600! cursor-not-allowed pointer-events-none';
