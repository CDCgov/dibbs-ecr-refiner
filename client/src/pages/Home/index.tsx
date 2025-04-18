import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { Link } from 'react-router';
import DibbsLogo from '../../assets/dibbs-logo.svg';

async function refine(unrefinedEicr: string): Promise<string> {
  if (!unrefinedEicr) {
    throw new Error('eICR XML must be provided as an input.');
  }
  const req = await fetch('/api/ecr', {
    body: unrefinedEicr,
    method: 'POST',
    headers: {
      'Content-Type': 'application/xml',
    },
  });
  const result = await req.text();
  return result;
}

export function Home() {
  const [eicr, setEicr] = useState('');
  const [refinedEicr, setRefinedEicr] = useState('');
  const [error, setError] = useState('');

  const { mutate } = useMutation({
    mutationFn: refine,
    onSuccess: (data) => {
      setRefinedEicr(data);
    },
    onError: (error) => {
      setError(error.message);
    },
  });

  function onReset(): void {
    setRefinedEicr('');
    setError('');
  }

  return (
    <div className="flex min-h-screen min-w-full flex-col gap-10 bg-blue-500 p-6 text-white">
      <header className="flex items-center gap-20">
        <Link to="/">
          <h1 className="flex gap-3">
            <img src={DibbsLogo} alt="DIBBs" />
            <span className="text-2xl">eCR Refiner</span>
          </h1>
        </Link>
        <nav>
          <Link className="hover:underline" to="demo">
            Demo
          </Link>
        </nav>
      </header>
      <div className="flex flex-col gap-4">
        <div className="flex gap-4">
          <button
            className="cursor-pointer rounded border-1 border-transparent bg-blue-300 px-4 px-6 text-xl font-bold text-white hover:border-1 hover:border-white/80"
            onClick={() => mutate(eicr)}
          >
            Refine eICR
          </button>
          <button
            className="cursor-pointer rounded border-1 border-transparent bg-blue-300 px-4 px-6 text-xl font-bold text-white hover:border-1 hover:border-white/80"
            onClick={onReset}
          >
            Reset
          </button>
        </div>
        <div>{error ? <p className="bg-yellow-800 p-2">{error}</p> : null}</div>
        <div className="flex gap-4">
          <div className="flex min-w-1/2 flex-col">
            <label htmlFor="input">Unrefined eICR:</label>
            <textarea
              className="min-h-screen bg-gray-300 text-black"
              id="input"
              onChange={(e) => {
                e.preventDefault();
                setEicr(e.target.value);
              }}
              onClick={() => setError('')}
              onBlur={() => setError('')}
            />
          </div>
          <div className="flex min-w-1/2 flex-col">
            <label htmlFor="output">Refined eICR:</label>
            <textarea
              className="min-h-screen bg-gray-600"
              id="output"
              disabled
              value={refinedEicr}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
