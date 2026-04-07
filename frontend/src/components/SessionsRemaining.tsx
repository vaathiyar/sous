import { useSessionsRemaining } from '@/hooks/useSessionsRemaining';

export function SessionsRemaining() {
  const data = useSessionsRemaining();
  if (!data) return null;

  const remaining = data.sessions_limit - data.sessions_used;
  const isLow = remaining <= 1;

  return (
    <span className={`sessions-remaining${isLow ? ' sessions-remaining--low' : ''}`}>
      {remaining} session{remaining !== 1 ? 's' : ''} left
    </span>
  );
}
