import classNames from 'classnames';
import { NavLinkProps, NavLink } from 'react-router';

interface StepsContainer {
  children: React.ReactNode;
}

export function StepsContainer({ children }: StepsContainer) {
  return (
    <div className="flex min-h-14 items-center gap-4 rounded-lg py-4">
      {children}
    </div>
  );
}

interface StepsProps {
  configurationId: string;
}

export function Steps({ configurationId }: StepsProps) {
  return (
    <ol className="flex list-inside flex-col gap-11 sm:flex-row sm:gap-10">
      <li>
        <StepLink to={`/configurations/${configurationId}/build`}>
          Build
        </StepLink>
      </li>
      <li>
        <StepLink to={`/configurations/${configurationId}/test`}>Test</StepLink>
      </li>
      {/* TODO: Uncomment this when we want to show the 'Activate' page again. */}
      {/* <li>
        <StepLink to={`/configurations/${configurationId}/activate`}>
          Activate
        </StepLink>
      </li> */}
    </ol>
  );
}

function StepLink({ to, className, children, ...props }: NavLinkProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        classNames('text-blue-cool-80 hover:underline', className, {
          'border-blue-cool-30 text-blue-cool-80 border-b-4 pb-1 font-bold':
            isActive,
        })
      }
      {...props}
    >
      {children}
    </NavLink>
  );
}
