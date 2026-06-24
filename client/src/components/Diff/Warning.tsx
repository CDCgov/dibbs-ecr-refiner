type WarningProps = {
  heading: string;
  message: string;
};

export function Warning({ heading, message }: WarningProps) {
  return (
    <div className="text-state-error-dark bg-state-error-lighter flex w-100 items-start p-4">
      <div className="flex gap-4">
        <WarningIcon />
        <div className="flex flex-col gap-2">
          <p className="font-bold">{heading}</p>
          <p>{message}</p>
        </div>
      </div>
    </div>
  );
}

function WarningIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="28"
      height="20"
      viewBox="0 0 24 24"
      fill="currentColor"
    >
      <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
    </svg>
  );
}
