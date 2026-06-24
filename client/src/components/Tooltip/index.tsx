// TODO: Consider adopting a floating-ui-based positioning approach and add
// snapshot tests
import { useState, useRef, useId } from 'react';
import { Portal, Transition } from '@headlessui/react';
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

const BOUNDING_GAP = 8;

type PositionConfig = {
  top: (r: DOMRect) => number;
  left: (r: DOMRect) => number;
  transform: string;
};

const POSITION_MAPPING: Record<TooltipPosition, PositionConfig> = {
  top: {
    left: (r) => r.left + r.width / 2,
    top: (r) => r.top - BOUNDING_GAP,
    transform: 'translate(-50%, -100%)',
  },
  bottom: {
    left: (r) => r.left + r.width / 2,
    top: (r) => r.bottom + BOUNDING_GAP,
    transform: 'translateX(-50%)',
  },
  left: {
    left: (r) => r.left - BOUNDING_GAP,
    top: (r) => r.top + r.height / 2,
    transform: 'translate(-100%, -50%)',
  },
  right: {
    left: (r) => r.right + BOUNDING_GAP,
    top: (r) => r.top + r.height / 2,
    transform: 'translateY(-50%)',
  },
};

function getTooltipStyle(
  position: TooltipPosition,
  rect: DOMRect | null
): React.CSSProperties {
  if (!rect) return { position: 'fixed', visibility: 'hidden' };
  const config = POSITION_MAPPING[position];
  return {
    position: 'fixed',
    left: config.left(rect),
    top: config.top(rect),
    transform: config.transform,
  };
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

function InfoIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="none"
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M9.16675 5.83366H10.8334V7.50033H9.16675V5.83366ZM9.16675 9.16699H10.8334V14.167H9.16675V9.16699ZM10.0001 1.66699C5.40008 1.66699 1.66675 5.40033 1.66675 10.0003C1.66675 14.6003 5.40008 18.3337 10.0001 18.3337C14.6001 18.3337 18.3334 14.6003 18.3334 10.0003C18.3334 5.40033 14.6001 1.66699 10.0001 1.66699ZM10.0001 16.667C6.32508 16.667 3.33341 13.6753 3.33341 10.0003C3.33341 6.32533 6.32508 3.33366 10.0001 3.33366C13.6751 3.33366 16.6667 6.32533 16.6667 10.0003C16.6667 13.6753 13.6751 16.667 10.0001 16.667Z"
        fill="#3A7D95"
      />
    </svg>
  );
}
