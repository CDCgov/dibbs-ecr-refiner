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
    <div>
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <button onClick={() => mutate(eicr)}>Refine eICR</button>
        <button onClick={onReset}>Reset</button>
      </div>
      {error ? <p>{error}</p> : null}
      <div className="io-container">
        <div style={{ width: '50%' }}>
          <label htmlFor="input">Unrefined eICR:</label>
          <textarea
            id="input"
            style={{ minWidth: '100%', minHeight: '100%' }}
            onChange={(e) => {
              e.preventDefault();
              setEicr(e.target.value);
            }}
            onClick={() => setError('')}
            onBlur={() => setError('')}
          />
        </div>
        <div style={{ minWidth: '50%' }}>
          <label htmlFor="output">Refined eICR:</label>
          <textarea
            id="output"
            style={{ minWidth: '100%', minHeight: '100%' }}
            disabled
            value={refinedEicr}
          />
        </div>
      </div>
    </div>
  );
}
