import React from 'react';
import classNames from 'classnames';

export const LAYOUT_MAX_WIDTH = 'max-w-[1200px]';

type LayoutPadding = 'none' | 'sm' | 'md' | 'lg' | 'xl';

const PADDING_MAP: Record<LayoutPadding, string> = {
  none: '',
  sm: 'px-4 py-3',
  md: 'px-8 py-4',
  lg: 'px-8 lg:px-20 py-6',
  xl: 'px-12 lg:px-24 py-8',
};

interface LayoutContainerProps {
  /** The content to be rendered inside the container */
  children: React.ReactNode;
  /**
   * The maximum width of the container.
   * Defaults to LAYOUT_MAX_WIDTH.
   */
  maxWidth?: typeof LAYOUT_MAX_WIDTH | 'max-w-7xl' | 'max-w-full';

  /** Additional CSS classes for the inner container */
  className?: string;
  /** Tailwind background class for the container */
  background?: string;

  /** When true, use breakout CSS for full-width effect */
  breakout?: boolean;
  /**
   * Structured padding level.
   * Defaults to 'lg'.
   */
  padding?: LayoutPadding;
}

/**
 * LayoutContainer provides a consistent way to handle max-width,
 * centering, and background extension across the application.
 */
export function LayoutContainer({
  children,
  maxWidth = LAYOUT_MAX_WIDTH,
  className,
  background,
  breakout = false,
  padding = 'lg',
}: LayoutContainerProps) {
  const paddingClasses = PADDING_MAP[padding];

  // If breakout is true, we use the banner-breakout utility.
  if (breakout) {
    return (
      <div className={classNames('banner-breakout', background)}>
        <div
          className={classNames(
            'banner-breakout-content mx-auto w-full',
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

  // Otherwise, the container itself carries the background and is centered.
  return (
    <div
      className={classNames(
        'mx-auto w-full',
        maxWidth,
        paddingClasses,
        background,
        className
      )}
    >
      {children}
    </div>
  );
}
