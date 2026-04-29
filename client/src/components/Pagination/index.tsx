/**
 * Based on @trussworks/react-uswds Pagination component
 * https://github.com/trussworks/react-uswds/blob/main/src/components/Pagination/Pagination.tsx
 */
import React, { type JSX } from 'react';
import classNames from 'classnames';

export type PaginationProps = {
  pathname: string;
  totalPages?: number;
  currentPage: number;
  maxSlots?: number;
  onClickNext?: () => void;
  onClickPrevious?: () => void;
  onClickPageNumber?: (
    event: React.MouseEvent<HTMLButtonElement>,
    page: number
  ) => void;
} & JSX.IntrinsicElements['nav'];

export function Pagination({
  pathname,
  totalPages,
  currentPage,
  className,
  maxSlots = 7,
  onClickPrevious,
  onClickNext,
  onClickPageNumber,
  ...props
}: PaginationProps) {
  const isOnFirstPage = currentPage === 1;
  const isOnLastPage = totalPages ? currentPage === totalPages : false;

  const showOverflow = totalPages ? totalPages > maxSlots : true;

  const middleSlot = Math.round(maxSlots / 2);
  const isBeforeMiddleSlot = !!(
    totalPages && totalPages - currentPage >= middleSlot
  );
  const showPrevOverflow = showOverflow && currentPage > middleSlot;
  const showNextOverflow = isBeforeMiddleSlot || !totalPages;

  const currentPageRange: Array<number | 'overflow'> =
    showOverflow || !totalPages
      ? [currentPage]
      : Array.from({ length: totalPages }).map((_, i) => i + 1);

  if (showOverflow) {
    const prevSlots = isOnFirstPage ? 0 : showPrevOverflow ? 2 : 1;
    const nextSlots = isOnLastPage ? 0 : showNextOverflow ? 2 : 1;
    const pageRangeSize = maxSlots - 1 - (prevSlots + nextSlots);

    let currentPageBeforeSize = 0;
    let currentPageAfterSize = 0;

    if (showPrevOverflow && showNextOverflow) {
      currentPageBeforeSize = Math.round((pageRangeSize - 1) / 2);
      currentPageAfterSize = pageRangeSize - currentPageBeforeSize;
    } else if (showPrevOverflow) {
      currentPageAfterSize = Math.max(0, (totalPages || 0) - currentPage - 1);
      currentPageBeforeSize = pageRangeSize - currentPageAfterSize;
    } else if (showNextOverflow) {
      currentPageBeforeSize = Math.max(0, currentPage - 2);
      currentPageAfterSize = pageRangeSize - currentPageBeforeSize;
    }

    let counter = 1;
    while (currentPageBeforeSize > 0) {
      currentPageRange.unshift(currentPage - counter++);
      currentPageBeforeSize--;
    }

    counter = 1;
    while (currentPageAfterSize > 0) {
      currentPageRange.push(currentPage + counter++);
      currentPageAfterSize--;
    }

    if (showPrevOverflow) currentPageRange.unshift('overflow');
    if (currentPage !== 1) currentPageRange.unshift(1);
    if (showNextOverflow) currentPageRange.push('overflow');
    if (totalPages && currentPage !== totalPages)
      currentPageRange.push(totalPages);
  }

  const prevPage = !isOnFirstPage && currentPage - 1;
  const nextPage = !isOnLastPage && currentPage + 1;

  const prevNextBase = classNames(
    'relative inline-flex items-center gap-1 px-3 h-10 rounded hover:cursor-pointer',
    'text-blue-cool-60 underline underline-offset-4'
  );

  return (
    <nav
      aria-label="Pagination"
      className={classNames('flex items-center justify-center', className)}
      {...props}
    >
      <ul className="flex list-none items-center gap-2">
        {prevPage && (
          <li>
            {onClickPrevious ? (
              <button
                type="button"
                className={prevNextBase}
                aria-label="Previous page"
                data-testid="pagination-previous"
                onClick={onClickPrevious}
              >
                <ChevronLeft />
                Previous
              </button>
            ) : (
              <a
                href={`${pathname}?page=${prevPage}`}
                className={prevNextBase}
                aria-label="Previous page"
              >
                <ChevronLeft />
                Previous
              </a>
            )}
          </li>
        )}

        {currentPageRange.map((pageNum, i) =>
          pageNum === 'overflow' ? (
            <PaginationOverflow key={`overflow_${i}`} />
          ) : (
            <PaginationPage
              key={`page_${pageNum}`}
              page={pageNum}
              pathname={pathname}
              isCurrent={pageNum === currentPage}
              onClickPageNumber={onClickPageNumber}
            />
          )
        )}

        {nextPage && (
          <li>
            {onClickNext ? (
              <button
                type="button"
                className={prevNextBase}
                aria-label="Next page"
                data-testid="pagination-next"
                onClick={onClickNext}
              >
                Next
                <ChevronRight />
              </button>
            ) : (
              <a
                href={`${pathname}?page=${nextPage}`}
                className={prevNextBase}
                aria-label="Next page"
              >
                Next
                <ChevronRight />
              </a>
            )}
          </li>
        )}
      </ul>
    </nav>
  );
}

interface SvgContainerProps {
  children: React.ReactNode;
}
function SvgContainer({ children }: SvgContainerProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="1.1em"
      height="1.1em"
      viewBox="0 0 24 24"
      focusable="false"
      role="img"
      aria-hidden="true"
      fill="#2e6276"
    >
      {children}
    </svg>
  );
}

function ChevronLeft() {
  return (
    <SvgContainer>
      <path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z"></path>
    </SvgContainer>
  );
}

function ChevronRight() {
  return (
    <SvgContainer>
      <path d="M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"></path>
    </SvgContainer>
  );
}

function PaginationPage({
  page,
  isCurrent,
  pathname,
  onClickPageNumber,
}: {
  pathname: string;
  page: number;
  isCurrent?: boolean;
  onClickPageNumber?: (
    event: React.MouseEvent<HTMLButtonElement>,
    page: number
  ) => void;
}) {
  const baseClasses = classNames(
    'relative inline-flex items-center justify-center w-10 h-10 font-medium rounded hover:cursor-pointer underline',
    {
      'z-10 bg-blue-cool-80 underline text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600':
        isCurrent,
    },
    {
      'text-blue-cool-60 ring-1 ring-inset ring-gray-400 hover:ring-gray-600 focus:outline-offset-0':
        !isCurrent,
    }
  );

  return (
    <li>
      {onClickPageNumber ? (
        <button
          type="button"
          className={baseClasses}
          aria-label={`Page ${page}`}
          aria-current={isCurrent ? 'page' : undefined}
          onClick={(e) => onClickPageNumber(e, page)}
        >
          {page}
        </button>
      ) : (
        <a
          href={`${pathname}?page=${page}`}
          className={baseClasses}
          aria-label={`Page ${page}`}
          aria-current={isCurrent ? 'page' : undefined}
        >
          {page}
        </a>
      )}
    </li>
  );
}

function PaginationOverflow() {
  return (
    <li aria-label="ellipsis indicating non-visible pages">
      <span className="relative inline-flex h-10 w-10 items-center justify-center text-gray-700 select-none">
        &hellip;
      </span>
    </li>
  );
}
