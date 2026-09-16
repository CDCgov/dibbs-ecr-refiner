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
      <Table striped>
        <TableBody>
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
    expect(tbody).toHaveClass('[&>tr:nth-child(even)]:bg-gray-cool-5');
  });

  it('applies bordered class to TableBody and TableHead when prop is passed', () => {
    const { container } = render(
      <Table bordered>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Header</TableHeaderCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>1</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
    const tbody = container.querySelector('tbody');
    expect(tbody).toHaveClass('divide-y');
    expect(tbody).toHaveClass('divide-gray-cool-20');

    const thead = container.querySelector('thead');
    expect(thead).toHaveClass('border-b-2');
    expect(thead).toHaveClass('border-gray-cool-70');
  });

  it('applies sticky class to TableHead when prop is passed', () => {
    const { container } = render(
      <Table stickyHeader>
        <TableHead>
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
});
