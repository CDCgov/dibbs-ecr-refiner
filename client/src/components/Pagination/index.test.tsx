import { render, screen } from '@testing-library/react';
import { Pagination, PaginationProps } from '.';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';

const renderPagination = (props: PaginationProps) =>
  render(
    <MemoryRouter>
      <Pagination {...props} />
    </MemoryRouter>
  );

describe('Pagination component', () => {
  const TOTAL_PAGES = 24;
  const THREE_PAGES = 3;
  const SEVEN_PAGES = 7;
  const TEST_PATHNAME = '/test-pathname';
  const DEFAULT_MAX_SLOTS = 7;
  const TOTAL_ITEMS_WITH_NAV = DEFAULT_MAX_SLOTS + 2; // prev + 7 slots + next

  const defaultProps: PaginationProps = {
    totalPages: TOTAL_PAGES,
    currentPage: 10,
    pathname: TEST_PATHNAME,
  };

  const expectPageLink = (label: string, href: string) => {
    expect(screen.getByLabelText(label)).toHaveAttribute('href', href);
  };

  it('renders pagination for a list of pages', () => {
    renderPagination(defaultProps);

    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expectPageLink('Previous page', `${TEST_PATHNAME}?page=9`);
    expectPageLink('Page 1', `${TEST_PATHNAME}?page=1`);
    expectPageLink('Page 9', `${TEST_PATHNAME}?page=9`);
    expectPageLink('Page 10', `${TEST_PATHNAME}?page=10`);
    expectPageLink('Page 11', `${TEST_PATHNAME}?page=11`);
    expectPageLink('Page 24', `${TEST_PATHNAME}?page=24`);
    expectPageLink('Next page', `${TEST_PATHNAME}?page=11`);
  });

  it('only renders the maximum number of slots', () => {
    renderPagination(defaultProps);
    expect(screen.getAllByRole('listitem')).toHaveLength(TOTAL_ITEMS_WITH_NAV);
  });

  it('marks only the current page with aria-current', () => {
    renderPagination(defaultProps);
    expect(screen.getByLabelText('Page 10')).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(screen.getByLabelText('Page 9')).not.toHaveAttribute('aria-current');
    expect(screen.getByLabelText('Page 11')).not.toHaveAttribute(
      'aria-current'
    );
  });

  it('hides the Previous button on the first page', () => {
    renderPagination({ ...defaultProps, currentPage: 1 });
    expect(screen.queryByLabelText('Previous page')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Next page')).toBeInTheDocument();
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'aria-current',
      'page'
    );
  });

  it('hides the Next button on the last page', () => {
    renderPagination({ ...defaultProps, currentPage: 24 });
    expect(screen.queryByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.queryByLabelText('Next page')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'aria-current',
      'page'
    );
  });

  it('renders overflow at both ends when current page is in the middle', () => {
    renderPagination(defaultProps);
    expect(screen.getAllByText('…')).toHaveLength(2);
  });

  it('renders overflow only at the end when near the start', () => {
    renderPagination({ ...defaultProps, currentPage: 3 });

    expectPageLink('Previous page', `${TEST_PATHNAME}?page=2`);
    expectPageLink('Page 1', `${TEST_PATHNAME}?page=1`);
    expectPageLink('Page 2', `${TEST_PATHNAME}?page=2`);
    expectPageLink('Page 3', `${TEST_PATHNAME}?page=3`);
    expectPageLink('Page 4', `${TEST_PATHNAME}?page=4`);
    expectPageLink('Page 5', `${TEST_PATHNAME}?page=5`);
    expectPageLink('Page 24', `${TEST_PATHNAME}?page=24`);
    expectPageLink('Next page', `${TEST_PATHNAME}?page=4`);
    expect(screen.getAllByText('…')).toHaveLength(1);
  });

  it('renders overflow only at the start when near the end', () => {
    renderPagination({ ...defaultProps, currentPage: 21 });

    expectPageLink('Previous page', `${TEST_PATHNAME}?page=20`);
    expectPageLink('Page 1', `${TEST_PATHNAME}?page=1`);
    expectPageLink('Page 20', `${TEST_PATHNAME}?page=20`);
    expectPageLink('Page 21', `${TEST_PATHNAME}?page=21`);
    expectPageLink('Page 22', `${TEST_PATHNAME}?page=22`);
    expectPageLink('Page 23', `${TEST_PATHNAME}?page=23`);
    expectPageLink('Page 24', `${TEST_PATHNAME}?page=24`);
    expectPageLink('Next page', `${TEST_PATHNAME}?page=22`);
    expect(screen.getAllByText('…')).toHaveLength(1);
  });

  it("doesn't render last page when unbounded", () => {
    const UNBOUNDED_PAGE = 500;
    renderPagination({
      ...defaultProps,
      totalPages: undefined,
      currentPage: UNBOUNDED_PAGE,
    });
    expect(screen.getByLabelText(`Page ${UNBOUNDED_PAGE + 1}`)).toHaveAttribute(
      'href',
      `${TEST_PATHNAME}?page=${UNBOUNDED_PAGE + 1}`
    );
  });

  it('calls onClickNext, onClickPrevious, and onClickPageNumber when clicked', async () => {
    const user = userEvent.setup();
    const mockOnClickNext = vi.fn();
    const mockOnClickPrevious = vi.fn();
    const mockOnClickPageNumber = vi.fn();

    renderPagination({
      ...defaultProps,
      currentPage: 21,
      onClickPrevious: mockOnClickPrevious,
      onClickNext: mockOnClickNext,
      onClickPageNumber: mockOnClickPageNumber,
    });

    await user.click(screen.getByRole('button', { name: 'Next page' }));
    expect(mockOnClickNext).toHaveBeenCalledTimes(1);

    await user.click(screen.getByRole('button', { name: 'Previous page' }));
    expect(mockOnClickPrevious).toHaveBeenCalledTimes(1);

    const allPageNumbers = screen.getAllByRole('button', {
      name: /^Page \d+$/,
    });
    await user.click(allPageNumbers[0]);
    expect(mockOnClickPageNumber).toHaveBeenCalledTimes(1);
  });

  it('renders no overflow when totalPages is less than maxSlots (3 pages)', () => {
    renderPagination({
      ...defaultProps,
      totalPages: THREE_PAGES,
      currentPage: 2,
    });
    expect(screen.getAllByRole('listitem')).toHaveLength(THREE_PAGES + 2); // prev + 3 pages + next
    expect(screen.queryAllByText('…')).toHaveLength(0);
  });

  it('renders no overflow when totalPages equals maxSlots (7 pages)', () => {
    renderPagination({
      ...defaultProps,
      totalPages: SEVEN_PAGES,
      currentPage: 4,
    });
    expect(screen.getAllByRole('listitem')).toHaveLength(TOTAL_ITEMS_WITH_NAV);
    expect(screen.queryAllByText('…')).toHaveLength(0);
  });

  it('only renders the maximum number of slots', () => {
    const CUSTOM_MAX_SLOTS = 10;
    renderPagination({ ...defaultProps, maxSlots: CUSTOM_MAX_SLOTS });
    expect(screen.getAllByRole('listitem')).toHaveLength(CUSTOM_MAX_SLOTS + 2); // prev + 10 slots + next
  });
});
