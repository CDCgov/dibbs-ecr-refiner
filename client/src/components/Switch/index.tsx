import { Switch as HeadlessSwitch, SwitchProps as HeadlessSwitchProps } from '@headlessui/react';
import classNames from 'classnames';

interface CustomSwitchProps extends HeadlessSwitchProps {
  variant?: 'violet' | 'blue';
}

export function Switch({ variant = 'violet', ...props }: CustomSwitchProps) {
  const checkedBgClass =
    variant === 'violet'
      ? 'data-checked:bg-violet-warm-60'
      : 'data-checked:bg-blue-cool-50';

  return (
    <HeadlessSwitch
      className={classNames(
        'group bg-gray-cool-30 inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition data-disabled:cursor-not-allowed data-disabled:opacity-50',
        checkedBgClass
      )}
      {...props}
    >
      <span className="data-disabled:bg-gray-cool-60 pointer-events-none size-4 translate-x-1 rounded-full bg-white transition group-data-checked:translate-x-6" />
    </HeadlessSwitch>
  );
}
