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
  maxSlots = 7, // USWDS default behavior assumes odd window
  onClickNext,
  onClickPrevious,
  onClickPageNumber,
}: PaginationProps) {
  const halfWindow = Math.floor((maxSlots - 3) / 2);

  const showLeftEllipsis = currentPage > halfWindow + 2;
  const showRightEllipsis = currentPage < totalPages - (halfWindow + 1);

  const startPage = Math.max(2, currentPage - halfWindow);

  const endPage = Math.min(totalPages - 1, currentPage + halfWindow);

  const hidePrevious = currentPage === 1;
  const hideNext = currentPage === totalPages;

  return (
    <nav className="usa-pagination" aria-label="Pagination">
      <ul className="usa-pagination__list flex items-center justify-center">
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

        {/* Page 1 */}
        <li className="usa-pagination__item usa-pagination__page-no">
          <button
            type="button"
            className={`usa-pagination__button ${
              currentPage === 1 ? 'usa-current' : ''
            }`}
            aria-current={currentPage === 1 ? 'page' : undefined}
            onClick={(e) => onClickPageNumber(e, 1)}
          >
            1
          </button>
        </li>

        {/* Left ellipsis */}
        {showLeftEllipsis && (
          <li
            className="usa-pagination__item usa-pagination__overflow"
            aria-hidden="true"
          >
            <span>…</span>
          </li>
        )}

        {/* Middle pages */}
        {Array.from(
          { length: endPage - startPage + 1 },
          (_, i) => startPage + i
        ).map((page) => (
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

        {/* Right ellipsis */}
        {showRightEllipsis && (
          <li
            className="usa-pagination__item usa-pagination__overflow"
            aria-hidden="true"
          >
            <span>…</span>
          </li>
        )}

        {/* Last page */}
        {totalPages > 1 && (
          <li className="usa-pagination__item usa-pagination__page-no">
            <button
              type="button"
              className={`usa-pagination__button ${
                currentPage === totalPages ? 'usa-current' : ''
              }`}
              aria-current={currentPage === totalPages ? 'page' : undefined}
              onClick={(e) => onClickPageNumber(e, totalPages)}
            >
              {totalPages}
            </button>
          </li>
        )}

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
