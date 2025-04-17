import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';

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
    <div className="flex flex-col gap-4 min-w-full">
      <div className="flex gap-4 min-w-1/2">
        <button
          className="text-white text-xl font-bold bg-blue-300 border-1 border-transparent hover:border-white/80 hover:border-1 px-6 px-4 rounded cursor-pointer"
          onClick={() => mutate(eicr)}
        >
          Refine eICR
        </button>
        <button
          className="text-white text-xl font-bold bg-blue-300 border-1 border-transparent hover:border-white/80 hover:border-1 px-6 px-4 rounded cursor-pointer"
          onClick={onReset}
        >
          Reset
        </button>
      </div>
      <div>{error ? <p className="bg-yellow-800 p-2">{error}</p> : null}</div>
      <div className="flex min-w-full gap-4">
        <div className="flex flex-col min-w-1/2">
          <label htmlFor="input">Unrefined eICR:</label>
          <textarea
            className="bg-gray-300 min-h-screen text-black"
            id="input"
            onChange={(e) => {
              e.preventDefault();
              setEicr(e.target.value);
            }}
            onClick={() => setError('')}
            onBlur={() => setError('')}
          />
        </div>
        <div className="flex flex-col min-w-1/2">
          <label htmlFor="output">Refined eICR:</label>
          <textarea
            className="bg-gray-600 min-h-screen"
            id="output"
            disabled
            value={refinedEicr}
          />
        </div>
      </div>
    </div>
  );
}
