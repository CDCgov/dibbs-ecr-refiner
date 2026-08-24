import React from 'react';
import classNames from 'classnames';

export const LAYOUT_MAX_WIDTH = 'max-w-[1200px]';

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
    * Tailwind padding classes.

   * Defaults to 'px-8 lg:px-20'.
   */
  padding?: string;
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
  padding = 'px-8 lg:px-20',
}: LayoutContainerProps) {
  // If breakout is true, we use the banner-breakout utility.
  if (breakout) {
    return (
      <div className={classNames('banner-breakout', background)}>
        <div
          className={classNames(
            'banner-breakout-content mx-auto w-full',
            maxWidth,
            padding,
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
        padding,
        background,
        className
      )}
    >
      {children}
    </div>
  );
}
