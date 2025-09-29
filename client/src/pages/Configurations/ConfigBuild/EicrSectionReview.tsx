import React from 'react';
import Table from '../../../components/Table';
import { DbConfigurationSectionProcessing } from '../../../api/schemas/dbConfigurationSectionProcessing';

/**
 * EicrSectionReview displays an overview or review of eICR sections.
 * This is a placeholder implementation. Replace with real content as needed.
 */
const EicrSectionReview: React.FC<{
  sectionProcessing: DbConfigurationSectionProcessing[];
}> = ({ sectionProcessing }) => {
  return (
    <section
      aria-label="Choose what you'd like to do with the sections in your eICR"
      className="prose w-full"
    >
      <h2 className="!mb-4 text-lg leading-10 font-bold">
        Choose what you'd like to do with the sections in your eICR
      </h2>
      <p className="!mb-4">
        Choose whether to refine, include fully, or omit sections of your eICR
        to save space and protect patient privacy.
      </p>
      <p className="!mb-2 leading-8">Options:</p>
      <ul className="!mb-4 list-inside list-disc pl-4">
        <li>
          <b>Include & refine section:</b> Includes only the coded data you've
          chosen to retain in your configuration.
        </li>
        <li>
          <b>Include entire section:</b> Includes everything from this section,
          ignoring your configuration.
        </li>
        <li>
          <b>Remove section:</b> Excludes this section from the eICR entirely.
        </li>
      </ul>
      {/* USWDS Table Component */}
      <Table bordered fullWidth className="margin-top-2" scrollable>
        <caption className="usa-sr-only">
          Choose actions for each eICR section
        </caption>
        <thead>
          <tr>
            <th scope="col">Section name</th>
            <th scope="col">Include &amp; refine section</th>
            <th scope="col">Include entire section</th>
            <th scope="col">Remove section</th>
          </tr>
        </thead>
        <tbody>
          {sectionProcessing.map((section, index) => (
            <tr key={section.name}>
              <td>{section.name}</td>
              <td className="text-center">
                <input
                  type="radio"
                  name={`action-${index}`}
                  value="retain"
                  aria-label={`Include and refine section ${section.name}`}
                />
              </td>
              <td className="text-center">
                <input
                  type="radio"
                  name={`action-${index}`}
                  value="refine"
                  aria-label={`Include entire section ${section.name}`}
                />
              </td>
              <td className="text-center">
                <input
                  type="radio"
                  name={`action-${index}`}
                  value="remove"
                  aria-label={`Remove section ${section.name}`}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </section>
  );
};

export default EicrSectionReview;
