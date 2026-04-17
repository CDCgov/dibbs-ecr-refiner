import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useState } from 'react';
import { Combobox, ComboboxInput, ComboboxOption, ComboboxOptions } from '.';
import { GetConditionsResponse } from '../../api/schemas/getConditionsResponse';

type Option = GetConditionsResponse;

const options: Option[] = [
  { id: '1', display_name: 'Influenza' },
  { id: '2', display_name: 'COVID-19' },
  { id: '3', display_name: 'Tuberculosis' },
];

interface TestComboboxProps {
  onSelect?: (v: Option | null) => void;
}

// minimal component to test combobox functionality
function TestCombobox({ onSelect }: TestComboboxProps) {
  const [selected, setSelected] = useState<Option | null>(null);
  const [query, setQuery] = useState('');

  const filtered =
    query === ''
      ? options
      : options.filter((o) =>
          o.display_name.toLowerCase().includes(query.toLowerCase())
        );

  function handleChange(value: Option | null) {
    setSelected(value);
    onSelect?.(value);
  }

  return (
    <Combobox
      value={selected}
      onChange={handleChange}
      onClose={() => setQuery('')}
    >
      <ComboboxInput<Option>
        aria-label="Select condition"
        displayValue={(o) => o?.display_name ?? ''}
        onChange={(e) => setQuery(e.target.value)}
        hasValue={!!selected}
        onClear={() => {
          handleChange(null);
          setQuery('');
        }}
      />
      <ComboboxOptions>
        {filtered.map((option) => (
          <ComboboxOption key={option.id} value={option}>
            {option.display_name}
          </ComboboxOption>
        ))}
      </ComboboxOptions>
    </Combobox>
  );
}

describe('Combobox', () => {
  it('renders the input', () => {
    render(<TestCombobox />);
    expect(
      screen.getByRole('combobox', { name: /select condition/i })
    ).toBeInTheDocument();
  });

  it('opens the dropdown on input click', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    expect(await screen.findByRole('listbox')).toBeInTheDocument();
  });

  it('shows all options when opened', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    expect(
      await screen.findByRole('option', { name: 'Influenza' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: 'COVID-19' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: 'Tuberculosis' })
    ).toBeInTheDocument();
  });

  it('filters options by query', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.type(
      screen.getByRole('combobox', { name: /select condition/i }),
      'cov'
    );
    expect(
      await screen.findByRole('option', { name: 'COVID-19' })
    ).toBeInTheDocument();
    expect(
      screen.queryByRole('option', { name: 'Influenza' })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole('option', { name: 'Tuberculosis' })
    ).not.toBeInTheDocument();
  });

  it('displays the selected option in the input', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'Influenza' }));
    expect(
      screen.getByRole('combobox', { name: /select condition/i })
    ).toHaveValue('Influenza');
  });

  it('calls onChange with the selected option', async () => {
    const onSelect = vi.fn();
    const user = userEvent.setup();
    render(<TestCombobox onSelect={onSelect} />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'COVID-19' }));
    expect(onSelect).toHaveBeenCalledWith({
      id: '2',
      display_name: 'COVID-19',
    });
  });

  it('does not show the clear button when nothing is selected', () => {
    render(<TestCombobox />);
    expect(
      screen.queryByRole('button', { name: /clear selection/i })
    ).not.toBeInTheDocument();
  });

  it('shows the clear button when a value is selected', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'Influenza' }));
    expect(
      screen.getByRole('button', { name: /clear selection/i })
    ).toBeInTheDocument();
  });

  it('clears the selection when the clear button is clicked', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(<TestCombobox onSelect={onSelect} />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'Influenza' }));
    await user.click(screen.getByRole('button', { name: /clear selection/i }));
    expect(
      screen.getByRole('combobox', { name: /select condition/i })
    ).toHaveValue('');
    expect(onSelect).toHaveBeenLastCalledWith(null);
  });

  it('hides the clear button after clearing', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'Influenza' }));
    await user.click(screen.getByRole('button', { name: /clear selection/i }));
    expect(
      screen.queryByRole('button', { name: /clear selection/i })
    ).not.toBeInTheDocument();
  });

  it('resets the query when the dropdown closes', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.type(
      screen.getByRole('combobox', { name: /select condition/i }),
      'cov'
    );
    await user.keyboard('{Escape}');
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    expect(
      await screen.findByRole('option', { name: 'Influenza' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('option', { name: 'COVID-19' })
    ).toBeInTheDocument();
  });

  it('restores focus to the input after clearing', async () => {
    const user = userEvent.setup();
    render(<TestCombobox />);
    await user.click(
      screen.getByRole('combobox', { name: /select condition/i })
    );
    await user.click(await screen.findByRole('option', { name: 'Influenza' }));
    await user.click(screen.getByRole('button', { name: /clear selection/i }));
    expect(
      screen.getByRole('combobox', { name: /select condition/i })
    ).toHaveFocus();
  });
});
