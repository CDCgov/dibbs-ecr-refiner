import { useState, useRef, useId } from 'react';
import { Transition } from '@headlessui/react';
import { InfoIcon } from './InfoIcon';
import classNames from 'classnames';

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  label: string;
  position?: TooltipPosition;
}

const positionClasses: Record<TooltipPosition, string> = {
  top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
  bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
  left: 'right-full top-1/2 -translate-y-1/2 mr-2',
  right: 'left-full top-1/2 -translate-y-1/2 ml-2',
};

const arrowClasses: Record<TooltipPosition, string> = {
  top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-[#1b1b1b]',
  bottom:
    'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-[#1b1b1b]',
  left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-[#1b1b1b]',
  right:
    'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-[#1b1b1b]',
};

export function Tooltip({ label, position = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const tooltipId = useId();
  const showTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  function show() {
    showTimeout.current = setTimeout(() => setVisible(true), 300);
  }

  function hide() {
    if (showTimeout.current) clearTimeout(showTimeout.current);
    setVisible(false);
  }

  return (
    <span className="relative inline-flex items-center">
      <button
        type="button"
        aria-describedby={tooltipId}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={hide}
        className="inline-flex cursor-default rounded-sm focus:outline-2 focus:outline-offset-2 focus:outline-blue-600"
      >
        <span aria-hidden>
          <InfoIcon />
        </span>
        <span className="sr-only">More information</span>
      </button>

      <Transition
        show={visible}
        enter="transition-opacity duration-150 ease-in"
        enterFrom="opacity-0"
        enterTo="opacity-100"
        leave="transition-opacity duration-100 ease-out"
        leaveFrom="opacity-100"
        leaveTo="opacity-0"
      >
        <span
          id={tooltipId}
          role="tooltip"
          className={classNames(
            'bg-gray-90 pointer-events-none absolute z-50 w-max max-w-xs rounded-sm p-2 font-normal text-white',
            positionClasses[position]
          )}
        >
          {label}
          <span
            aria-hidden
            className={classNames(
              'absolute h-0 w-0 border-4 border-solid',
              arrowClasses[position]
            )}
          />
        </span>
      </Transition>
    </span>
  );
}
