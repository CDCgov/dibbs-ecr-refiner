interface LayoutProps {
  children: React.ReactNode;
}
export function Layout({ children }: LayoutProps) {
  return <main className="flex flex-1">{children}</main>;
}
