import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import {
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
} from './index';

describe('Table Component', () => {
  it('renders a full table with correct semantic HTML tags', () => {
    render(
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Header 1</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>Cell 1</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
    expect(screen.getAllByRole('rowgroup')).toHaveLength(2); // thead/tbody
    expect(screen.getByRole('columnheader')).toHaveTextContent('Header 1');
    expect(screen.getByRole('cell')).toHaveTextContent('Cell 1');
  });

  it('defaults TableHeaderCell scope to "col"', () => {
    render(
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Header</TableHeaderCell>
          </TableRow>
        </TableHead>
      </Table>
    );
    expect(screen.getByRole('columnheader')).toHaveAttribute('scope', 'col');
  });

  it('allows overriding TableHeaderCell scope to "row"', () => {
    render(
      <Table>
        <TableBody>
          <TableRow>
            <TableHeaderCell scope="row">Row Header</TableHeaderCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(screen.getByRole('rowheader')).toHaveAttribute('scope', 'row');
  });

  it('applies striped class to TableBody when prop is passed', () => {
    const { container } = render(
      <Table>
        <TableBody striped>
          <TableRow>
            <TableCell>1</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>2</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    const tbody = container.querySelector('tbody');
    expect(tbody).toHaveClass('[&>tr:nth-child(even)]:bg-gray-cool-2');
  });

  it('applies rounded class to presentation div when prop is passed', () => {
    render(<Table rounded>Content</Table>);
    const presentationDiv = screen.getByRole('presentation');
    expect(presentationDiv).toHaveClass('overflow-hidden rounded-lg');
  });

  it('applies border to presentation div when both bordered and rounded props are passed', () => {
    render(
      <Table bordered rounded>
        Content
      </Table>
    );
    const presentationDiv = screen.getByRole('presentation');
    expect(presentationDiv).toHaveClass('border-gray-cool-30 border');
  });

  it('applies border to table element when bordered prop is passed without rounded', () => {
    const { container } = render(<Table bordered>Content</Table>);
    const table = container.querySelector('table');
    expect(table).toHaveClass('border-gray-cool-30 border');

    const presentationDiv = screen.getByRole('presentation');
    expect(presentationDiv).not.toHaveClass('border-gray-cool-30 border');
  });

  it('applies border-b to TableHead when bordered prop is passed', () => {
    const { container } = render(
      <Table>
        <TableHead bordered>
          <TableRow>
            <TableHeaderCell>Header</TableHeaderCell>
          </TableRow>
        </TableHead>
      </Table>
    );
    const thead = container.querySelector('thead');
    expect(thead).toHaveClass('border-gray-cool-40 border-b');
  });

  it('applies row border classes to TableBody when bordered prop is passed', () => {
    const { container } = render(
      <Table>
        <TableBody bordered>
          <TableRow>
            <TableCell>1</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    const tbody = container.querySelector('tbody');
    expect(tbody).toHaveClass(
      '[&>tr:not(:last-child)]:border-gray-cool-60 [&>tr:not(:last-child)]:border-b'
    );
  });

  it('applies sticky class to TableHead when prop is passed', () => {
    const { container } = render(
      <Table>
        <TableHead stickyHeader>
          <TableRow>
            <TableHeaderCell>Header</TableHeaderCell>
          </TableRow>
        </TableHead>
      </Table>
    );
    const thead = container.querySelector('thead');
    expect(thead).toHaveClass('sticky');
    expect(thead).toHaveClass('top-0');
    expect(thead).toHaveClass('z-sticky');
  });

  it('merges custom className with default classes', () => {
    const { container } = render(
      <Table className="custom-table">
        <TableHead className="custom-head">
          <TableRow>
            <TableHeaderCell className="custom-cell">Header</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody className="custom-body">
          <TableRow>
            <TableCell className="custom-td">Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    expect(container.querySelector('table')).toHaveClass(
      'w-full',
      'custom-table'
    );
    expect(container.querySelector('thead')).toHaveClass('custom-head');
    expect(container.querySelector('th')).toHaveClass('px-4', 'custom-cell');
    expect(container.querySelector('tbody')).toHaveClass('custom-body');
    expect(container.querySelector('td')).toHaveClass('px-4', 'custom-td');
  });

  it('passes through standard td attributes like colSpan', () => {
    render(
      <Table>
        <TableBody>
          <TableRow>
            <TableCell colSpan={2}>Spanned Cell</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(screen.getByText('Spanned Cell')).toHaveAttribute('colspan', '2');
  });

  it('passes through standard tr attributes like aria-label to TableRow', () => {
    render(
      <Table>
        <TableBody>
          <TableRow aria-label="Log entry">
            <TableCell>Entry 1</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    expect(screen.getByRole('row', { name: 'Log entry' })).toBeInTheDocument();
  });

  it('allows TableHeaderCell to render with no children', () => {
    render(
      <Table>
        <TableHead>
          <TableRow>
            <TableHeaderCell />
          </TableRow>
        </TableHead>
      </Table>
    );
    expect(screen.getByRole('columnheader')).toBeInTheDocument();
  });

  describe('maxWidth prop', () => {
    const testCases = [
      { prop: 'sm', expectedClass: 'max-w-96' },
      { prop: 'md', expectedClass: 'max-w-302' },
      { prop: 'lg', expectedClass: 'max-w-4xl' },
      { prop: 'full', expectedClass: 'max-w-full' },
    ];

    testCases.forEach(({ prop, expectedClass }) => {
      it(`applies ${expectedClass} when maxWidth is "${prop}"`, () => {
        const { container } = render(
          <Table maxWidth={prop as any}>
            <TableBody>
              <TableRow>
                <TableCell>Content</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        );
        const table = container.querySelector('table');
        expect(table).toHaveClass(expectedClass);
      });
    });

    it('does not apply maxWidth class when prop is not provided', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const table = container.querySelector('table');
      expect(table).not.toHaveClass(
        'max-w-96',
        'max-w-302',
        'max-w-4xl',
        'max-w-full'
      );
    });
  });

  describe('layout prop', () => {
    it('applies table-auto by default', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const table = container.querySelector('table');
      expect(table).toHaveClass('table-auto');
    });

    it('applies table-fixed when layout="fixed" is passed', () => {
      const { container } = render(
        <Table layout="fixed">
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const table = container.querySelector('table');
      expect(table).toHaveClass('table-fixed');
      expect(table).not.toHaveClass('table-auto');
    });
  });

  describe('cellHeight prop', () => {
    const testCases = [
      { prop: 'compact', expectedClass: '[&_tbody_td]:h-12' },
      { prop: 'normal', expectedClass: '[&_tbody_td]:h-17' },
      { prop: 'spacious', expectedClass: '[&_tbody_td]:h-20' },
    ];

    testCases.forEach(({ prop, expectedClass }) => {
      it(`applies ${expectedClass} when cellHeight is "${prop}"`, () => {
        const { container } = render(
          <Table cellHeight={prop as any}>
            <TableBody>
              <TableRow>
                <TableCell>Content</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        );
        const table = container.querySelector('table');
        expect(table).toHaveClass(expectedClass);
      });
    });

    it('defaults to normal cellHeight', () => {
      const { container } = render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Content</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      const table = container.querySelector('table');
      expect(table).toHaveClass('[&_tbody_td]:h-17');
    });
  });

  it('applies hover classes to tbody rows when hover prop is passed', () => {
    const { container } = render(
      <Table hover>
        <TableBody>
          <TableRow>
            <TableCell>Content</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    const table = container.querySelector('table');
    expect(table).toHaveClass('[&_tbody_tr:hover]:bg-gray-200');
  });

  it('applies border-spacing-0 and removes border-collapse when borderless prop is passed', () => {
    const { container } = render(
      <Table borderless>
        <TableBody>
          <TableRow>
            <TableCell>Content</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    const table = container.querySelector('table');
    expect(table).toHaveClass('border-spacing-0');
    expect(table).not.toHaveClass('border-collapse');
  });

  describe('TableCell size prop', () => {
    it('applies text-sm when size="sm" is passed', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell size="sm">Small Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Small Cell')).toHaveClass('text-sm');
      expect(screen.getByText('Small Cell')).not.toHaveClass('text-base');
    });

    it('applies text-base when size="base" is passed', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell size="base">Base Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Base Cell')).toHaveClass('text-base');
      expect(screen.getByText('Base Cell')).not.toHaveClass('text-sm');
    });

    it('defaults to text-base when size prop is not provided', () => {
      render(
        <Table>
          <TableBody>
            <TableRow>
              <TableCell>Default Cell</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByText('Default Cell')).toHaveClass('text-base');
    });
  });
});
