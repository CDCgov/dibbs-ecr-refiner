export function NavigationContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 px-8 pt-8 pb-6 sm:justify-between lg:px-20">
      {children}
    </div>
  );
}

export function SectionContainer({ children }: { children: React.ReactNode }) {
  return <section className="px-8 pt-8 pb-6 lg:px-20">{children}</section>;
}

export function TitleContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white px-8 pt-8 pb-6 shadow-lg lg:px-20">{children}</div>
  );
}
