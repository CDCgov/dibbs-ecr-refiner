import { Label as HeadlessLabel, LabelProps } from '@headlessui/react';
import classNames from 'classnames';

function Label({ className, ...props }: LabelProps) {
  return <HeadlessLabel className={classNames(className)} {...props} />;
}

export { Label, type LabelProps };
