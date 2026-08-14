import { Spinner } from '@components/Spinner';
import {
  Combobox,
  ComboboxButton,
  ComboboxOptions,
  ComboboxOption,
} from '@headlessui/react';
import { useGetCodeFilters } from '../../../api/configurations/configurations';

const CLEAR_OPTION = { id: '__clear__', label: '' } as const;

export interface FilterOption {
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
  const handleChange = (values: (T | typeof CLEAR_OPTION)[]) => {
    if (values.some((v) => v.id === CLEAR_OPTION.id)) {
      onChange([]);
    } else {
      onChange(values as T[]);
    }
  };

  return (
    <Combobox multiple value={selected} onChange={handleChange}>
      {({ open }) => (
        <div className="relative">
          <ComboboxButton className="flex w-44 items-center justify-between gap-6 border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-800 shadow-sm hover:cursor-pointer focus:ring-2 focus:ring-blue-500 focus:outline-none">
            {selected.length <= 0 ? (
              label
            ) : (
              <span>{selected.length} selected</span>
            )}
            <span className="flex items-center gap-2 border-l border-gray-300 pl-3">
              <ChevronDownIcon />
            </span>
          </ComboboxButton>

          {open && (
            <div className="absolute left-0 z-100 mt-1 w-56 rounded-md border border-gray-300! bg-white shadow-lg">
              <ComboboxOptions
                static
                className="max-h-100 overflow-y-scroll py-1 focus:outline-none"
              >
                {options.map((option) => (
                  <ComboboxOption
                    key={option.id}
                    value={option}
                    className="ui-active:bg-gray-50 hover:bg-blue-cool-5 cursor-pointer px-4 py-2 select-none"
                  >
                    {({ selected }) => (
                      <div className="flex items-center gap-3">
                        <span
                          aria-hidden="true"
                          className={`flex size-4 shrink-0 items-center justify-center border ${
                            selected
                              ? 'border-violet-warm-60 bg-violet-warm-60'
                              : 'border-gray-400 bg-white'
                          }`}
                        >
                          {selected && (
                            <svg
                              className="stroke-white"
                              viewBox="0 0 14 14"
                              fill="none"
                            >
                              <path
                                d="M3 8L6 11L11 3.5"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          )}
                        </span>
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

                {/*
                  This needs special handling to be a valid ComboboxOption.
                */}
                <ComboboxOption
                  value={CLEAR_OPTION}
                  className="mt-1 border-t border-gray-300 px-4 pt-2 pb-1"
                >
                  <span className="text-blue-cool-50 hover:text-blue-cool-70 font-bold hover:cursor-pointer hover:underline">
                    Clear selection
                  </span>
                </ComboboxOption>
              </ComboboxOptions>
            </div>
          )}
        </div>
      )}
    </Combobox>
  );
}

function ChevronDownIcon() {
  return (
    <svg
      aria-hidden
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
    id: f.condition_id ?? f.source,
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
