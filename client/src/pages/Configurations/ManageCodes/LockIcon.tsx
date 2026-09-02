interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
  color?: string;
}

export function LockIcon({
  size = 18,
  color = '#71767a',
  ...props
}: IconProps) {
  return (
    <svg
      data-testid="lock-icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={color}
      {...props}
    >
      <path d="M18 8h-1V6A5 5 0 0 0 7 6v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2zM9 6a3 3 0 0 1 6 0v2H9V6zm3 11a2 2 0 1 1 0-4 2 2 0 0 1 0 4z" />
    </svg>
  );
}
