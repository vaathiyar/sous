import { useState, useEffect } from 'react';
import { BarVisualizer, useVoiceAssistant, useLocalParticipant } from '@livekit/components-react';
import { MicIcon, MicOffIcon } from '@/components/icons';

const STATE_LABELS: Record<string, string> = {
  disconnected: 'Waiting…',
  connecting:   'Connecting…',
  initializing: 'Getting ready…',
  listening:    'Listening',
  thinking:     'Thinking…',
  speaking:     'Speaking',
};

interface AgentViewProps {
  recipeTitle: string;
  onEnd: () => void;
}

export function AgentView({ recipeTitle, onEnd }: AgentViewProps) {
  const { state, audioTrack } = useVoiceAssistant();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const [agentHasSpoken, setAgentHasSpoken] = useState(false);

  useEffect(() => {
    if (state === 'speaking') setAgentHasSpoken(true);
  }, [state]);

  const toggleMic = () => {
    localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  };

  const label = STATE_LABELS[state] ?? state;

  const pillClass = `state-pill${
    state === 'speaking'  ? ' state-pill--speaking'  :
    state === 'listening' ? ' state-pill--listening' : ''
  }`;

  const micClass = `mic-btn ${isMicrophoneEnabled ? 'mic-btn--live' : 'mic-btn--muted'}`;

  return (
    <div className="session-page">
      <header className="session-header">
        <span className="wordmark">Suvai</span>
        <span className="session-recipe">{recipeTitle}</span>
        <span className={pillClass}>{label}</span>
      </header>

      <section className="visualizer-section">
        <div className="viz-container">
          <BarVisualizer
            state={state}
            trackRef={audioTrack}
            style={{ width: '100%', height: '100%' }}
          />
        </div>
        <p className="agent-hint">
          {!agentHasSpoken        ? 'Waiting for chef…'        :
           state === 'speaking'   ? 'Chef is talking…'         :
           state === 'listening'  ? 'Go ahead, I\'m listening' :
           'Waiting for chef…'}
        </p>
      </section>

      <div className="session-controls">
        <button
          className={micClass}
          onClick={toggleMic}
          aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
        >
          {isMicrophoneEnabled ? <MicIcon /> : <MicOffIcon />}
        </button>
        <p className="mic-hint">
          {isMicrophoneEnabled ? 'Tap to mute' : 'Tap to unmute'}
        </p>
        <button className="end-btn" onClick={onEnd}>
          End Session
        </button>
      </div>
    </div>
  );
}
