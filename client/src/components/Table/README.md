# Table Component

The `Table` component is a compound component used to render semantic HTML tables. It replaces the previous `@trussworks/react-uswds` Table wrapper and raw `<table>` elements to ensure consistent styling using TailwindCSS.

## API Reference

### `Table`

The root component that provides context for styling flags.

- `children`: `React.ReactNode`
- `className`: `string` (optional)
- `striped`: `boolean` (optional) - Adds zebra-striping to rows in `TableBody`.
- `bordered`: `boolean` (optional) - Adds a bottom border to `TableHead` and horizontal dividers between rows in `TableBody`.
- `stickyHeader`: `boolean` (optional) - Makes the `TableHead` sticky at the top of the container.

### `TableHead`

Renders the `<thead>` element.

- `children`: `React.ReactNode`
- `className`: `string` (optional)

### `TableBody`

Renders the `<tbody>` element.

- `children`: `React.ReactNode`
- `className`: `string` (optional)

### `TableRow`

Renders the `<tr>` element.

- `children`: `React.ReactNode`
- `className`: `string` (optional)

### `TableHeaderCell`

Renders the `<th>` element.

- `children`: `React.ReactNode`
- `className`: `string` (optional)
- `scope`: `'col' | 'row'` (optional, defaults to `'col'`)

### `TableCell`

Renders the `<td>` element.

- `children`: `React.ReactNode`
- `className`: `string` (optional)
- Supports all standard `<td>` attributes (e.g., `colSpan`, `data-label`).

## Migration Guide

### From USWDS Table Wrapper

The previous `Table` component was a wrapper that accepted props like `striped` and `fullWidth`. It is now a compound component.

**Before:**

```tsx
<Table className="table-auto" striped fullWidth>
  <thead>
    <tr>
      <th scope="col">Name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Foo</td>
    </tr>
  </tbody>
</Table>
```

**After:**

```tsx
<Table className="table-auto" striped>
  <TableHead>
    <TableRow>
      <TableHeaderCell>Name</TableHeaderCell>
    </TableRow>
  </TableHead>
  <TableBody>
    <TableRow>
      <TableCell>Foo</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

### From Native HTML Table

Replace native tags with the compound components to ensure consistent baseline styling.

**Before:**

```tsx
<table className="w-full table-auto">
  <thead>
    <tr>
      <th scope="col">Name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Foo</td>
    </tr>
  </tbody>
</table>
```

**After:**

```tsx
<Table className="table-auto">
  <TableHead>
    <TableRow>
      <TableHeaderCell>Name</TableHeaderCell>
    </TableRow>
  </TableHead>
  <TableBody>
    <TableRow>
      <TableCell>Foo</TableCell>
    </TableRow>
  </TableBody>
</Table>
```

## Notes

- **Captions**: There is no `TableCaption` component. Use a raw `<caption>` element as a direct child of `Table`.
- **Features**: This component is presentational only. It does not include built-in sorting, pagination, selection, or responsive stacked views.

## Legacy Table Look

Some pages still need to match the previous USWDS-table-derived visual style (rounded outer border, subtle gray header, row separators, hover highlight). For these cases, apply the `legacy-table` class (plus optionally `legacy-table--borderless` / `legacy-table--striped`) via the `className` prop:

```tsx
<Table className="legacy-table legacy-table--borderless">
```

This is a stopgap to preserve visual parity during the migration to the compound `Table` component, not a long-term recommended pattern for new tables. See `client/src/tailwind.css` for the source of these classes.
