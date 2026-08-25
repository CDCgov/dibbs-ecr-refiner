import React from 'react';
import classNames from 'classnames';
import { LAYOUT_MAX_WIDTH } from './LayoutContainer';

type LayoutPadding = 'none' | 'sm' | 'md' | 'lg' | 'xl';

const PADDING_MAP: Record<LayoutPadding, string> = {
  none: '',
  sm: 'px-4',
  md: 'px-8',
  lg: 'px-8 lg:px-20',
  xl: 'px-12 lg:px-24',
};

interface AlertBreakoutContainerProps {
  /** The content to be rendered inside the container */
  children: React.ReactNode;
  /** Tailwind background class for the outer breakout wrapper */
  background?: string;
  /**
   * The maximum width of the inner content wrapper.
   * Defaults to LAYOUT_MAX_WIDTH.
   */
  maxWidth?: typeof LAYOUT_MAX_WIDTH | 'max-w-7xl' | 'max-w-full';
  /**
   * Structured padding level.
   * Defaults to 'lg'.
   */
  padding?: LayoutPadding;
  /** Additional CSS classes for the inner content wrapper */
  className?: string;
}

/**
 * AlertBreakoutContainer renders a full-width breakout band for alerts and notifications.
 * It ensures the background extends full-width while the content remains centered and constrained.
 */
export function AlertBreakoutContainer({
  children,
  background,
  maxWidth = LAYOUT_MAX_WIDTH,
  padding = 'lg',
  className,
}: AlertBreakoutContainerProps) {
  const paddingClasses = PADDING_MAP[padding];

  return (
    <div className={classNames('banner-breakout', background)}>
      <div
        className={classNames(
          'relative z-1 mx-auto w-full',
          maxWidth,
          paddingClasses,
          className
        )}
      >
        {children}
      </div>
    </div>
  );
}
