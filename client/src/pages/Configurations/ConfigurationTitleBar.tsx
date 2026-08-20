interface ConfigurationTitleBarProps {
  title: string;
  subtitle?: React.ReactNode;
}

export function ConfigurationTitleBar({
  title,
  subtitle,
}: ConfigurationTitleBarProps) {
  return (
    <div className="flex justify-start">
      <div className="flex flex-col">
        <div className="mb-2 flex items-center">
          <h2 className="text-gray-cool-90 mr-4 text-[1.75rem] font-bold">
            {title}
          </h2>
        </div>
        {subtitle ? <span>{subtitle}</span> : null}
      </div>
    </div>
  );
}
