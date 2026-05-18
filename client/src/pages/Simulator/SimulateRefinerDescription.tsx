import { Title } from '@components/Title';

/**
 * Renders the title and description for the Simulate Refiner module.
 * This is a reusable component for consistent module documentation.
 */
export const SimulateRefinerDescription = () => (
  <div className="mb-6 flex justify-start">
    <div className="flex flex-col">
      <Title>Simulate Refiner</Title>
      <p className="mt-2">
        This module allows you to simulate how the Refiner would work in
        production for a zipped eICR/RR pair input based on the reportable
        conditions your jurisdiction has configured.
      </p>
    </div>
  </div>
);
