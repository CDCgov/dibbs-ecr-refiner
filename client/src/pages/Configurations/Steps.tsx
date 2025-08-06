import classNames from 'classnames';
import { NavLinkProps, NavLink } from 'react-router';

interface StepsContainer {
  children: React.ReactNode;
}

export function StepsContainer({ children }: StepsContainer) {
  return (
    <div className="flex min-h-14 flex-col items-start gap-4 rounded-lg bg-white px-4 py-4 sm:py-2 md:flex-row md:items-center md:justify-between">
      {children}
    </div>
  );
}

interface StepsProps {
  configurationId: string;
}

export function Steps({ configurationId }: StepsProps) {
  return (
    <ol className="flex list-inside list-decimal flex-col gap-4 sm:flex-row sm:gap-10">
      <li>
        <StepLink to={`/configurations/${configurationId}/build`}>
          Build configuration
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/test`}>
          Test configuration
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/activate`}>
          Turn on configuration
        </StepLink>
      </li>
    </ol>
  );
}

function StepLink({ to, className, children, ...props }: NavLinkProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        classNames('text-blue-cool-60 hover:underline', className, {
          'font-bold text-black': isActive,
        })
      }
      {...props}
    >
      {children}
    </NavLink>
  );
}
