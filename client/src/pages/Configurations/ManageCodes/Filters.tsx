import { Button } from '@components/Button';
import { Spinner } from '@components/Spinner';
import {
  Combobox,
  ComboboxButton,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/react';
import { useGetCodeFilters } from '../../../api/configurations/configurations';
import { Checkbox } from '@components/Checkbox';

interface FilterOption {
  id: string | number;
  label: string;
  count?: number;
}

interface FilterComboboxProps<T extends FilterOption> {
  label: string;
  options: T[];
  selected: T[];
  onChange: (val: T[]) => void;
}

function FilterCombobox<T extends FilterOption>({
  label,
  options,
  selected,
  onChange,
}: FilterComboboxProps<T>) {
  return (
    <Combobox multiple value={selected} onChange={onChange} onClose={() => {}}>
      <div className="relative">
        <ComboboxButton className="flex w-44 items-center justify-between gap-6 border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm hover:cursor-pointer focus:ring-2 focus:ring-blue-500 focus:outline-none">
          {selected.length <= 0 ? (
            label
          ) : (
            <span>{selected.length} selected</span>
          )}
          <span
            aria-hidden
            className="flex items-center gap-2 border-l border-gray-300 pl-3"
          >
            <svg
              className="h-4 w-4 text-black"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                clipRule="evenodd"
              />
            </svg>
          </span>
        </ComboboxButton>

        <ComboboxOptions className="absolute left-0 z-100 mt-1 max-h-100 w-56 overflow-y-scroll rounded-md border border-gray-300! bg-white py-1 shadow-lg focus:outline-none">
          {options.map((option) => (
            <ComboboxOption
              key={option.id}
              value={option}
              className="ui-active:bg-gray-50 hover:bg-blue-cool-5 cursor-pointer px-4 py-2 select-none"
            >
              {({ selected }) => (
                <div className="flex items-center gap-3">
                  <Checkbox checked={selected} />
                  <span className="text-md flex-1 text-gray-800">
                    {option.label}
                  </span>
                  {option.count !== undefined && (
                    <span className="text-gray-cool-50 text-sm">
                      {option.count.toLocaleString()}
                    </span>
                  )}
                </div>
              )}
            </ComboboxOption>
          ))}

          <div className="mt-1 border-t border-gray-300 px-4 pt-2 pb-1">
            <Button
              variant="unstyled"
              onClick={() => onChange([])}
              className="text-blue-cool-50 hover:text-blue-cool-70 text-sm font-bold hover:cursor-pointer hover:underline"
            >
              Clear selection
            </Button>
          </div>
        </ComboboxOptions>
      </div>
    </Combobox>
  );
}

export interface CodeFilters {
  codeSystems: FilterOption[];
  sources: FilterOption[];
  statuses: FilterOption[];
}

interface FiltersProps {
  configurationId: string;
  filters: CodeFilters;
  onFiltersChange: (filters: CodeFilters) => void;
}

export function Filters({
  configurationId,
  filters,
  onFiltersChange,
}: FiltersProps) {
  const { data, isPending, isError } = useGetCodeFilters(configurationId);

  if (isPending) return <Spinner />;
  if (isError) return 'Error!';

  const { code_systems, sources, statuses } = data.data;

  const codeSystemOptions = code_systems.map((f) => ({
    id: f.system_id,
    label: f.system_name,
    count: f.code_count,
  }));

  const sourceOptions = sources.map((f) => ({
    id: f.condition_id,
    label: f.source,
    count: f.code_count,
  }));

  const statusOptions = statuses.map((f) => ({
    id: f.status,
    label: f.label,
    count: f.code_count,
  }));

  return (
    <div className="flex flex-col items-center gap-4 lg:flex-row">
      <span>Filter by:</span>
      <FilterCombobox
        label="Code system"
        options={codeSystemOptions}
        selected={filters.codeSystems}
        onChange={(val) => onFiltersChange({ ...filters, codeSystems: val })}
      />
      <FilterCombobox
        label="Source"
        options={sourceOptions}
        selected={filters.sources}
        onChange={(val) => onFiltersChange({ ...filters, sources: val })}
      />
      <FilterCombobox
        label="Status"
        options={statusOptions}
        selected={filters.statuses}
        onChange={(val) => onFiltersChange({ ...filters, statuses: val })}
      />
    </div>
  );
}
