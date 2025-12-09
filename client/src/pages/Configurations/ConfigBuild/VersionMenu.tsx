import { MenuButton, MenuItems, MenuItem, Menu } from '@headlessui/react';
import { Icon } from '@trussworks/react-uswds';
import { Link } from 'react-router';
import {
  GetConfigurationsResponseStatus,
  GetConfigurationResponseVersion,
} from '../../../api/schemas';
import { Fragment } from 'react';
import { useDatetimeFormatter } from '../../../hooks/UseDatetimeFormatter';

interface VersionMenuProps {
  id: string;
  currentVersion: number;
  status: GetConfigurationsResponseStatus;
  versions: GetConfigurationResponseVersion[];
  step: 'build' | 'test' | 'activate';
}

export function VersionMenu({
  currentVersion,
  status,
  versions,
  step,
}: VersionMenuProps) {
  return (
    <>
      <Menu as="div" className="z-10">
        <MenuButton>
          <div className="cursor-pointer">
            <span className="font-bold">
              {status === 'draft' ? 'Editing' : 'Viewing'}: Version{' '}
              {currentVersion}
            </span>
            <Icon.ArrowDropDown aria-hidden />
          </div>
        </MenuButton>
        <MenuItems className="absolute mt-1 ml-4 flex flex-col rounded-lg bg-white px-4 py-2 shadow-lg">
          {versions.map((v, i) => (
            <Fragment key={v.id}>
              <MenuItem>
                <Link
                  className="data-focus:bg-gray-10 block p-2"
                  to={`/configurations/${v.id}/${step}`}
                >
                  <div className="flex flex-col">
                    <VersionText
                      versionNumber={v.version}
                      isActive={v.status === 'active'}
                    />
                    <MenuItemDetail
                      className="text-gray-60"
                      created_at={v.created_at}
                      last_activated_at={v.last_activated_at}
                      created_by={v.created_by}
                    />
                  </div>
                </Link>
              </MenuItem>
              {versions.length - 1 !== i && (
                <div
                  aria-hidden
                  key={`${v.id}-divider`}
                  className="bg-gray-cool-10 my-1 h-px"
                ></div>
              )}
            </Fragment>
          ))}
        </MenuItems>
      </Menu>
      <div
        aria-hidden
        className="border-gray-cool-20 mx-1 hidden h-10 border-l md:block"
      ></div>
    </>
  );
}

interface VersionTextProps {
  versionNumber: number;
  isActive: boolean;
}

function VersionText({ versionNumber, isActive }: VersionTextProps) {
  const versionText = `Version ${versionNumber}`;
  return (
    <span className="text-gray-cool-90 font-bold">
      {versionText}{' '}
      {isActive ? (
        <span className="text-state-success-dark">(Active)</span>
      ) : null}
    </span>
  );
}

type MenuItemDetailProps = Pick<
  GetConfigurationResponseVersion,
  'created_at' | 'last_activated_at' | 'created_by'
> & {
  className?: string;
};
function MenuItemDetail({
  created_at,
  last_activated_at,
  created_by,
  className,
}: MenuItemDetailProps) {
  const formatDatetime = useDatetimeFormatter();

  if (last_activated_at) {
    const { date, time } = formatDatetime(last_activated_at);
    return (
      <span className={className}>
        Last activated {date}, {time} by {created_by}
      </span>
    );
  }

  const { date, time } = formatDatetime(created_at);

  return (
    <span className={className}>
      Draft created {date}, {time} by {created_by}
    </span>
  );
}
