// TODO: Consider adopting a floating-ui-based positioning approach and add
// snapshot tests
import { useState, useRef, useId } from 'react';
import { Portal, Transition } from '@headlessui/react';
import { InfoIcon } from './InfoIcon';
import classNames from 'classnames';

type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  label: string;
  position?: TooltipPosition;
}

const arrowClasses: Record<TooltipPosition, string> = {
  top: 'top-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-b-transparent border-t-[#1b1b1b]',
  bottom:
    'bottom-full left-1/2 -translate-x-1/2 border-l-transparent border-r-transparent border-t-transparent border-b-[#1b1b1b]',
  left: 'left-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-r-transparent border-l-[#1b1b1b]',
  right:
    'right-full top-1/2 -translate-y-1/2 border-t-transparent border-b-transparent border-l-transparent border-r-[#1b1b1b]',
};

function getTooltipStyle(
  position: TooltipPosition,
  rect: DOMRect | null
): React.CSSProperties {
  if (!rect) return { position: 'fixed', visibility: 'hidden' };

  const gap = 8;

  switch (position) {
    case 'top':
      return {
        position: 'fixed',
        left: rect.left + rect.width / 2,
        top: rect.top - gap,
        transform: 'translate(-50%, -100%)',
      };
    case 'bottom':
      return {
        position: 'fixed',
        left: rect.left + rect.width / 2,
        top: rect.bottom + gap,
        transform: 'translateX(-50%)',
      };
    case 'left':
      return {
        position: 'fixed',
        left: rect.left - gap,
        top: rect.top + rect.height / 2,
        transform: 'translate(-100%, -50%)',
      };
    case 'right':
      return {
        position: 'fixed',
        left: rect.right + gap,
        top: rect.top + rect.height / 2,
        transform: 'translateY(-50%)',
      };
  }
}

export function Tooltip({ label, position = 'top' }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const [triggerRect, setTriggerRect] = useState<DOMRect | null>(null);
  const tooltipId = useId();
  const showTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  function show() {
    if (triggerRef.current) {
      setTriggerRect(triggerRef.current.getBoundingClientRect());
    }
    showTimeout.current = setTimeout(() => setVisible(true), 300);
  }

  function hide() {
    if (showTimeout.current) clearTimeout(showTimeout.current);
    setVisible(false);
  }

  return (
    <span className="inline-flex items-center">
      <button
        ref={triggerRef}
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

      <Portal>
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
            style={getTooltipStyle(position, triggerRect)}
            className="bg-gray-90 pointer-events-none z-50 w-max max-w-xs rounded-sm p-2 font-normal text-white"
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
      </Portal>
    </span>
  );
}
