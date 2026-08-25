# Dropdown Z-Index Patterns

This guide documents the z-index system for dropdowns and overlays to prevent visual bugs where elements overlap incorrectly.

## Z-Index Hierarchy

We use a centralized z-index system defined in `client/src/styles/z-index.css`. All overlay components must use these CSS variables.

| Variable             | Value | Usage                          |
| :------------------- | :---- | :----------------------------- |
| `--z-base`           | 0     | Default page content           |
| `--z-sticky`         | 10    | Sticky headers/footers         |
| `--z-banner`         | 20    | Top-level notification banners |
| `--z-dropdown`       | 30    | Standard page-level dropdowns  |
| `--z-drawer`         | 40    | Side drawers/panels            |
| `--z-modal-backdrop` | 50    | Modal background dimming       |
| `--z-modal-content`  | 60    | Modal dialog boxes             |
| `--z-modal-dropdown` | 70    | Dropdowns inside modals        |

## Component Usage

### BaseDropdown vs HeadlessUI

Always prefer `BaseDropdown` components over direct `@headlessui/react` imports. `BaseDropdown` ensures the correct default z-index is applied.

#### ❌ Avoid (Direct HeadlessUI)

```tsx
import { Menu, MenuItems } from '@headlessui/react';

// This will likely be hidden behind other elements or
// overlap incorrectly because it lacks a z-index.
const MyDropdown = () => (
  <Menu>
    <MenuItems className="absolute bg-white">...</MenuItems>
  </Menu>
);
```

#### ✅ Prefer (BaseDropdown)

```tsx
import { BaseMenu, BaseMenuItems } from '@/components/Dropdown';

const MyDropdown = () => (
  <BaseMenu>
    <BaseMenuItems className="absolute bg-white">...</BaseMenuItems>
  </BaseMenu>
);
```

## Common Patterns

### 1. Page-Level Dropdowns

Use `BaseMenuItems` without overriding the z-index. It defaults to `var(--z-dropdown)`.

### 2. Dropdowns Inside Modals

Modals have a higher z-index (`--z-modal-content: 60`). A standard dropdown (`--z-dropdown: 30`) will appear _behind_ the modal. You must override the z-index to `var(--z-modal-dropdown)`.

```tsx
import { BaseMenu, BaseMenuItems } from '@/components/Dropdown';

const ModalDropdown = () => (
  <BaseMenu>
    <BaseMenuItems className="absolute z-[var(--z-modal-dropdown)] bg-white">
      {/* Content */}
    </BaseMenuItems>
  </BaseMenu>
);
```

## Migration Guide

When converting existing HeadlessUI dropdowns to the Base system:

1. Replace `Menu` with `BaseMenu`.
2. Replace `MenuButton` with `BaseMenuButton`.
3. Replace `MenuItems` with `BaseMenuItems`.
4. Remove any hardcoded `z-index` classes (e.g., `z-10`, `z-50`) and rely on the base component or the CSS variables.

## Troubleshooting Overlay Issues

If a dropdown is appearing behind another element:

1. **Check the Parent**: Does a parent element have `overflow: hidden` or `z-index` defined? This can create a new stacking context.
2. **Verify the Variable**: Inspect the element in DevTools. Is it using `z-[var(--z-dropdown)]`?
3. **Modal Context**: Is the dropdown inside a modal? If yes, ensure it uses `z-[var(--z-modal-dropdown)]`.
4. **Stacking Context**: If `z-index` seems ignored, check if a parent has `position: relative`, `absolute`, or `fixed` with a `z-index` that is lower than the surrounding elements.
