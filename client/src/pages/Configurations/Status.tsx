interface ConfigStatusProps {
  version: number | null;
}
export function ConfigStatus({ version }: ConfigStatusProps) {
  if (version) {
    return (
      <p className="text-state-success-dark font-bold">
        Status: Version {version} active
      </p>
    );
  }

  return <p className="text-gray-cool-60 font-bold">Status: Inactive</p>;
}
