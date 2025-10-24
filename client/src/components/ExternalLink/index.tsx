type ExternalLinkProps = Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'target'
> & {
  href: string;
};

export function ExternalLink({
  href,
  children,
  className,
  ...props
}: ExternalLinkProps) {
  const defaultStyling =
    'text-blue-cool-60 hover:text-blue-cool-50 underline underline-offset-2';
  return (
    <a
      className={className ? className : defaultStyling}
      href={href}
      target="_blank"
      {...props}
    >
      {children}
    </a>
  );
}
