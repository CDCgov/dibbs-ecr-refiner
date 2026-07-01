import classNames from 'classnames';

type ExternalLinkProps = Omit<
  React.AnchorHTMLAttributes<HTMLAnchorElement>,
  'target'
> & {
  href: string;
  includeIcon?: boolean;
};

export function ExternalLink({
  href,
  children,
  className,
  includeIcon = true,
  ...props
}: ExternalLinkProps) {
  const styles = classNames({
    'text-blue-cool-60 hover:text-blue-cool-50 underline underline-offset-2':
      !className,
  });
  return (
    <a className={styles} href={href} target="_blank" {...props}>
      {children}
      {includeIcon ? <LaunchIcon /> : null}
    </a>
  );
}

function LaunchIcon() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      width="1em"
      height="1em"
      viewBox="0 0 24 24"
      fill="currentColor"
      className="inline-block shrink-0 align-middle"
    >
      <path d="M19 19H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2v-7h-2v7zM14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3h-7z" />
    </svg>
  );
}
