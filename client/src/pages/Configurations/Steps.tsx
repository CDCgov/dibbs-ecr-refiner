import classNames from 'classnames';
import { NavLinkProps, NavLink } from 'react-router';

interface StepsContainer {
  children: React.ReactNode;
}

export function StepsContainer({ children }: StepsContainer) {
  return <div className="flex min-h-10 items-end py-1.5">{children}</div>;
}

interface StepsProps {
  configurationId: string;
}

export function Steps({ configurationId }: StepsProps) {
  return (
    <ol className="flex list-inside flex-col gap-8 sm:flex-row sm:gap-10">
      <li>
        <StepLink to={`/configurations/${configurationId}/customize-sections`}>
          Customize eICR sections
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/manage-codes`}>
          Manage codes
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/overrides`}>
          Apply overrides
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/test`}>
          Test & export
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
        classNames('text-blue-cool-80 hover:underline', className, {
          'border-blue-cool-30 text-blue-cool-80 -mb-1 border-b-4 pb-1 font-bold':
            isActive,
        })
      }
      {...props}
    >
      {children}
    </NavLink>
  );
}
