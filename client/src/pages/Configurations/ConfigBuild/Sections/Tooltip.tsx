import { Tooltip as USWDSTooltip } from '@trussworks/react-uswds';
import React, { JSX } from 'react';
import { InfoIcon } from './InfoIcon';

type CustomTooltipProps = JSX.IntrinsicElements['div'] &
  React.RefAttributes<HTMLDivElement>;
const CustomLinkForwardRef: React.ForwardRefRenderFunction<
  HTMLDivElement,
  CustomTooltipProps
> = ({ ...tooltipProps }: CustomTooltipProps, ref) => (
  <div {...tooltipProps} ref={ref}>
    <InfoIcon />
  </div>
);
const CustomTooltip = React.forwardRef(CustomLinkForwardRef);
interface TooltipProps {
  text: string;
}
export function Tooltip({ text }: TooltipProps) {
  return (
    <USWDSTooltip<CustomTooltipProps>
      position="left"
      label={<div className="w-max max-w-75 whitespace-normal">{text}</div>}
      asCustom={CustomTooltip}
    >
      Data handling approach tooltip
    </USWDSTooltip>
  );
}
