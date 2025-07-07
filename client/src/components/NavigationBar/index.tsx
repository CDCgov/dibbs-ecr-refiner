import classNames from 'classnames';
import { NavLink, NavLinkProps } from 'react-router';

export default function NavigationBar() {
  return (
    <nav
      aria-label="Primary navigation"
      className="usa-nav flex justify-end !text-lg text-white"
    >
      <NavigationLink to="/" title="Configurations" />
      <NavigationLink to="/testing" title="Testing" />
    </nav>
  );
}

type NavigationLinkProps = Pick<NavLinkProps, 'to' | 'title'>;

/**
 * NavigationLink is a function that wraps React Router's NavLink in a super generic way.
 */
function NavigationLink({ to, title }: NavigationLinkProps) {
  return (
<NavLink to={to} className="text-blue-cool-5">
      {({ isActive }) => (
        <span
          className={classNames('mx-6 inline-block py-1', {
            'border-b-4 border-blue-cool-30': isActive,
          })}
        >
          {title}
        </span>
      )}
    </NavLink>
  );
}
