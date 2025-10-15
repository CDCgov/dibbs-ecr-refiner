/**
 * A fixed, rotated, and accessible feedback button that links to the Touchpoints feedback form.
 * This component is positioned flush to the right edge of the viewport, rotated -90deg,
 * and provides accessible hover and focus-visible indications for mouse and keyboard users.
 */
export function ProvideFeedbackButton() {
  return (
    <div className="hover:bg-blue-cool-60 bg-blue-cool-80 fixed right-0 bottom-80 z-50 flex h-12 w-48 origin-bottom-right -rotate-90 transform cursor-pointer items-center justify-center text-white">
      <a
        href="https://touchpoints.app.cloud.gov/touchpoints/59d35058"
        target="_blank"
        rel="noreferrer noopener"
        className="hover:bg-blue-cool-60 flex h-full w-full items-center justify-center transition-colors hover:underline"
      >
        Provide Feedback
      </a>
    </div>
  );
}
