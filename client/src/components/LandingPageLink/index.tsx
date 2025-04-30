import { Link } from 'react-router';
import BackArrowSvg from '../../assets/back-arrow.svg';

export function LandingPageLink() {
  return (
    <Link
      className="flex items-center gap-2 self-start underline-offset-4 hover:underline"
      to="/"
    >
      <img src={BackArrowSvg} alt="" />
      <span>Return to landing page</span>
    </Link>
  );
}
