import { Icon } from '@trussworks/react-uswds';

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  maxSlots?: number;
  onClickNext: () => void;
  onClickPrevious: () => void;
  onClickPageNumber: (event: React.MouseEvent, pageNumber: number) => void;
};

export function Pagination({
  currentPage,
  totalPages,
  maxSlots = 6,
  onClickNext,
  onClickPrevious,
  onClickPageNumber,
}: PaginationProps) {
  const half = Math.floor(maxSlots / 2);

  const start = Math.max(
    1,
    Math.min(currentPage - half, totalPages - maxSlots + 1)
  );

  const end = Math.min(totalPages, start + maxSlots - 1);

  const pages = Array.from({ length: end - start + 1 }, (_, i) => start + i);

  const hidePrevious = currentPage === 1;
  const hideNext = currentPage === totalPages;

  return (
    <nav className="usa-pagination" aria-label="Pagination">
      <ul className="usa-pagination__list flex items-center justify-center gap-1">
        {/* Previous */}
        <li
          className="usa-pagination__item usa-pagination__arrow"
          style={{
            visibility: hidePrevious ? 'hidden' : 'visible',
            pointerEvents: hidePrevious ? 'none' : 'auto',
          }}
        >
          <button
            type="button"
            className="usa-pagination__link usa-pagination__previous-page"
            aria-label="Previous page"
            onClick={onClickPrevious}
          >
            <Icon.NavigateBefore />
            <span className="usa-pagination__link-text">Previous</span>
          </button>
        </li>

        {/* Page numbers */}
        {pages.map((page) => (
          <li
            key={page}
            className="usa-pagination__item usa-pagination__page-no"
          >
            <button
              type="button"
              className={`usa-pagination__button ${
                page === currentPage ? 'usa-current' : ''
              }`}
              aria-current={page === currentPage ? 'page' : undefined}
              onClick={(e) => onClickPageNumber(e, page)}
            >
              {page}
            </button>
          </li>
        ))}

        {/* Next */}
        <li
          className="usa-pagination__item usa-pagination__arrow"
          style={{
            visibility: hideNext ? 'hidden' : 'visible',
            pointerEvents: hideNext ? 'none' : 'auto',
          }}
        >
          <button
            type="button"
            className="usa-pagination__link usa-pagination__next-page"
            aria-label="Next page"
            onClick={onClickNext}
          >
            <span className="usa-pagination__link-text">Next</span>
            <Icon.NavigateNext />
          </button>
        </li>
      </ul>
    </nav>
  );
}
