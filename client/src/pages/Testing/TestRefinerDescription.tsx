import { Title } from '../../components/Title';
import React from 'react';

/**
 * Renders the title and description for the Test Refiner module.
 * This is a reusable component for consistent module documentation.
 */
export const TestRefinerDescription: React.FC = () => (
  <div className="mb-6 flex justify-start">
    <div className="flex flex-col">
      <Title>Test Refiner</Title>
      <p className="mt-2">
        This module allows you to simulate how the Refiner would work in
        production for a zipped eICR/RR pair input based on the reportable
        conditions your jurisdiction has configured.
      </p>
    </div>
  </div>
);
