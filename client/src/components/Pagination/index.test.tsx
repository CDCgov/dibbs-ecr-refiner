import { render, screen } from '@testing-library/react';
import { Pagination } from '.';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';

// const renderPagination = (props: PaginationProps) =>
//   render(
//     <MemoryRouter>
//       <Pagination {...props} />
//     </MemoryRouter>
//   )

describe('Pagination component', () => {
  const testPages = 24;
  const testThreePages = 3;
  const testSevenPages = 7;
  const testPathname = '/test-pathname';

  it('renders pagination for a list of pages', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={10}
          pathname={testPathname}
        />
      </MemoryRouter>
    );
    expect(screen.getByRole('navigation')).toBeInTheDocument();

    expect(screen.getByLabelText('Previous page')).toHaveAttribute(
      'href',
      `${testPathname}?page=9`
    );
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'href',
      `${testPathname}?page=1`
    );
    expect(screen.getByLabelText('Page 9')).toHaveAttribute(
      'href',
      `${testPathname}?page=9`
    );
    expect(screen.getByLabelText('Page 10')).toHaveAttribute(
      'href',
      `${testPathname}?page=10`
    );
    expect(screen.getByLabelText('Page 10')).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(screen.getByLabelText('Page 11')).toHaveAttribute(
      'href',
      `${testPathname}?page=11`
    );
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'href',
      `${testPathname}?page=24`
    );
    expect(screen.getByLabelText('Next page')).toHaveAttribute(
      'href',
      `${testPathname}?page=11`
    );
  });

  it('only renders the maximum number of slots', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={10}
          pathname={testPathname}
        />
      </MemoryRouter>
    );
    expect(screen.getAllByRole('listitem')).toHaveLength(9); // overflow slots don't count
  });

  it('renders pagination when the first page is current', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={1}
          pathname={testPathname}
        />
      </MemoryRouter>
    );
    expect(screen.queryByLabelText('Previous page')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Next page')).toBeInTheDocument();
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'aria-current',
      'page'
    );
  });

  it('renders pagination when the last page is current', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={24}
          pathname={testPathname}
        />
      </MemoryRouter>
    );
    expect(screen.queryByLabelText('Previous page')).toBeInTheDocument();
    expect(screen.queryByLabelText('Next page')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'aria-current',
      'page'
    );
  });

  it('renders overflow at the beginning and end when current page is in the middle', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={10}
          pathname={testPathname}
        />
      </MemoryRouter>
    );
    expect(screen.getByLabelText('Previous page')).toHaveAttribute(
      'href',
      `${testPathname}?page=9`
    );
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'href',
      `${testPathname}?page=1`
    );
    expect(screen.getByLabelText('Page 9')).toHaveAttribute(
      'href',
      `${testPathname}?page=9`
    );
    expect(screen.getByLabelText('Page 10')).toHaveAttribute(
      'href',
      `${testPathname}?page=10`
    );
    expect(screen.getByLabelText('Page 10')).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(screen.getByLabelText('Page 11')).toHaveAttribute(
      'href',
      `${testPathname}?page=11`
    );
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'href',
      `${testPathname}?page=24`
    );
    expect(screen.getByLabelText('Next page')).toHaveAttribute(
      'href',
      `${testPathname}?page=11`
    );
    expect(screen.getAllByText('…')).toHaveLength(2);
  });

  it('renders overflow at the end when at the beginning of the pages', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={3}
          pathname={testPathname}
        />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('Previous page')).toHaveAttribute(
      'href',
      `${testPathname}?page=2`
    );
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'href',
      `${testPathname}?page=1`
    );
    expect(screen.getByLabelText('Page 2')).toHaveAttribute(
      'href',
      `${testPathname}?page=2`
    );
    expect(screen.getByLabelText('Page 3')).toHaveAttribute(
      'href',
      `${testPathname}?page=3`
    );
    expect(screen.getByLabelText('Page 3')).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(screen.getByLabelText('Page 4')).toHaveAttribute(
      'href',
      `${testPathname}?page=4`
    );
    expect(screen.getByLabelText('Page 5')).toHaveAttribute(
      'href',
      `${testPathname}?page=5`
    );
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'href',
      `${testPathname}?page=24`
    );
    expect(screen.getByLabelText('Next page')).toHaveAttribute(
      'href',
      `${testPathname}?page=4`
    );
    expect(screen.getAllByText('…')).toHaveLength(1);
  });

  it('renders overflow at the beginning when at the end of the pages', () => {
    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={21}
          pathname={testPathname}
        />
      </MemoryRouter>
    );

    expect(screen.getByLabelText('Previous page')).toHaveAttribute(
      'href',
      `${testPathname}?page=20`
    );
    expect(screen.getByLabelText('Page 1')).toHaveAttribute(
      'href',
      `${testPathname}?page=1`
    );
    expect(screen.getByLabelText('Page 20')).toHaveAttribute(
      'href',
      `${testPathname}?page=20`
    );
    expect(screen.getByLabelText('Page 21')).toHaveAttribute(
      'href',
      `${testPathname}?page=21`
    );
    expect(screen.getByLabelText('Page 21')).toHaveAttribute(
      'aria-current',
      'page'
    );
    expect(screen.getByLabelText('Page 22')).toHaveAttribute(
      'href',
      `${testPathname}?page=22`
    );
    expect(screen.getByLabelText('Page 23')).toHaveAttribute(
      'href',
      `${testPathname}?page=23`
    );
    expect(screen.getByLabelText('Page 24')).toHaveAttribute(
      'href',
      `${testPathname}?page=24`
    );
    expect(screen.getByLabelText('Next page')).toHaveAttribute(
      'href',
      `${testPathname}?page=22`
    );
    expect(screen.getAllByText('…')).toHaveLength(1);
  });

  it("doesn't render last page when unbounded", () => {
    const randomPage = Math.random() * 1000;
    render(
      <MemoryRouter>
        <Pagination currentPage={randomPage} pathname={testPathname} />
      </MemoryRouter>
    );
    expect(screen.getByLabelText(`Page ${randomPage + 1}`)).toHaveAttribute(
      'href',
      `${testPathname}?page=${randomPage + 1}`
    );
  });

  it('can click onClickNext, onClickPrevious and onClickPagenumber', async () => {
    const user = userEvent.setup();
    const mockOnClickNext = vi.fn();
    const mockOnClickPrevious = vi.fn();
    const mockOnClickPageNumber = vi.fn();

    render(
      <MemoryRouter>
        <Pagination
          totalPages={testPages}
          currentPage={21}
          pathname={testPathname}
          onClickPrevious={mockOnClickPrevious}
          onClickNext={mockOnClickNext}
          onClickPageNumber={mockOnClickPageNumber}
        />
      </MemoryRouter>
    );

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

  describe('for fewer pages than the max slots', () => {
    it('renders pagination with no overflow 1', () => {
      render(
        <MemoryRouter>
          <Pagination
            totalPages={testThreePages}
            currentPage={2}
            pathname={testPathname}
          />
        </MemoryRouter>
      );
      expect(screen.getAllByRole('listitem')).toHaveLength(5);
      expect(screen.queryAllByText('…')).toHaveLength(0);
    });

    it('renders pagination with no overflow 2', () => {
      render(
        <MemoryRouter>
          <Pagination
            totalPages={testSevenPages}
            currentPage={4}
            pathname={testPathname}
          />
        </MemoryRouter>
      );
      expect(screen.getAllByRole('listitem')).toHaveLength(9);
      expect(screen.queryAllByText('…')).toHaveLength(0);
    });
  });

  describe('with a custom slot number passed in', () => {
    it('only renders the maximum number of slots', () => {
      render(
        <MemoryRouter>
          <Pagination
            totalPages={testPages}
            currentPage={10}
            pathname={testPathname}
            maxSlots={10}
          />
        </MemoryRouter>
      );
      expect(screen.getAllByRole('listitem')).toHaveLength(12);
    });
  });
});
