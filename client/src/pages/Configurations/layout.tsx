export function NavigationContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-blue-cool-5 drop-shadow-nav flex flex-col gap-4 px-8 sm:justify-between lg:px-20">
      {children}
    </div>
  );
}

export function SectionContainer({ children }: { children: React.ReactNode }) {
  return <section className="px-8 lg:px-20">{children}</section>;
}

export function TitleContainer({ children }: { children: React.ReactNode }) {
  return <div className="px-8 py-6 shadow-lg lg:px-20">{children}</div>;
}
