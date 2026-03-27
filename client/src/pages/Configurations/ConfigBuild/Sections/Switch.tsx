import { Switch as HeadlessSwitch, SwitchProps } from '@headlessui/react';
export function Switch({ ...props }: SwitchProps) {
  return (
    <HeadlessSwitch
      className="group data-checked:bg-violet-warm-60 bg-gray-cool-60 inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full transition data-disabled:cursor-not-allowed data-disabled:opacity-50"
      {...props}
    >
      <span className="data-disabled:bg-gray-cool-60 pointer-events-none size-4 translate-x-1 rounded-full bg-white transition group-data-checked:translate-x-6" />
    </HeadlessSwitch>
  );
}
