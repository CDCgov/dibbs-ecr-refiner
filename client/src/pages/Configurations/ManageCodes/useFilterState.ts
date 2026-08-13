import { useState, useMemo } from 'react';
import { useGetCodeFilters } from '../../../api/configurations/configurations';
import { CodeFilters, FilterOption } from './Filters';

export function useFilterState(configurationId: string) {
  const [filters, setFilters] = useState<CodeFilters>({
    codeSystems: [],
    sources: [],
    statuses: [],
  });

  const { data } = useGetCodeFilters(configurationId);

  const availableFilters = useMemo<CodeFilters>(() => {
    if (!data) return { codeSystems: [], sources: [], statuses: [] };
    const { code_systems, sources, statuses } = data.data;
    return {
      codeSystems: code_systems.map((f) => ({
        id: f.system_id,
        label: f.system_name,
        count: f.code_count,
      })),
      sources: sources.map((f) => ({
        id: f.condition_id ?? f.source,
        label: f.source,
        count: f.code_count,
      })),
      statuses: statuses.map((f) => ({
        id: f.status,
        label: f.label,
        count: f.code_count,
      })),
    };
  }, [data]);

  // match filters in use with filters that are available
  const activeFilters = useMemo(
    () => pruneFilters(filters, availableFilters),
    [filters, availableFilters]
  );

  return { filters: activeFilters, setFilters };
}

/**
 * Helper function to keep filter state in sync. Filters are pruned if they become
 * unavailable, such as if a code set is deleted while the source filter is in use.
 * @param filters user-selected filters
 * @param available filters available to select from
 * @returns
 */
function pruneFilters(
  filters: CodeFilters,
  available: CodeFilters
): CodeFilters {
  const keep = (selected: FilterOption[], options: FilterOption[]) => {
    const ids = new Set(options.map((o) => o.id));
    return selected.filter((s) => ids.has(s.id));
  };

  return {
    codeSystems: keep(filters.codeSystems, available.codeSystems),
    sources: keep(filters.sources, available.sources),
    statuses: keep(filters.statuses, available.statuses),
  };
}
