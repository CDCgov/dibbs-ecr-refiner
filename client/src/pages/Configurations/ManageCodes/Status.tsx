interface StatusProps {
  version: number | null;
}
export function Status({ version }: StatusProps) {
  if (version) {
    return (
      <p className="text-state-success-dark font-bold">
        <span
          className="bg-state-success-dark mr-1 inline-block h-3 w-3"
          aria-hidden
         />
        enabled
      </p>
    );
  }

  return (
    <p className="text-gray-cool-60 font-bold">
      <span
        className="bg-gray-cool-60 mr-1 inline-block h-3 w-3"
        aria-hidden
       />
      disabled
    </p>
  );
}
