import React from 'react';

/**
 * EicrSectionReview displays an overview or review of eICR sections.
 * This is a placeholder implementation. Replace with real content as needed.
 *
 * @component
 * @example
 * return <EicrSectionReview />
 */
const EicrSectionReview: React.FC = () => {
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
      {/* TODO: Replace with actual section content, data, or UI */}
      <div className="rounded border border-blue-100 bg-blue-50 p-4 text-blue-900">
        <p>Section content placeholder.</p>
      </div>
    </section>
  );
};

export default EicrSectionReview;
