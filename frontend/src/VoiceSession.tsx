import { useState, useEffect } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  useLocalParticipant,
  BarVisualizer,
} from "@livekit/components-react";
import "@livekit/components-styles";

interface Props {
  token: string;
  serverUrl: string;
  recipeTitle: string;
  onEnd: () => void;
}

// Mic on — filled microphone
function MicIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.91-3c-.49 0-.9.36-.98.85C16.52 14.2 14.47 16 12 16s-4.52-1.8-4.93-4.15c-.08-.49-.49-.85-.98-.85-.61 0-1.09.54-1 1.14.49 3 2.89 5.35 5.91 5.78V20c0 .55.45 1 1 1s1-.45 1-1v-2.08c3.02-.43 5.42-2.78 5.91-5.78.1-.6-.39-1.14-1-1.14z" />
    </svg>
  );
}

// Mic off — mic with diagonal slash
function MicOffIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19 11h-1.7c0 .74-.16 1.43-.43 2.05l1.23 1.23c.56-.98.9-2.09.9-3.28zm-4.02.17c0-.06.02-.11.02-.17V5c0-1.66-1.34-3-3-3S9 3.34 9 5v.18l5.98 5.99zM4.27 3 3 4.27l6.01 6.01V11c0 1.66 1.34 3 3 3 .23 0 .44-.03.65-.08l1.66 1.66c-.71.33-1.5.52-2.31.52-2.76 0-5.3-2.1-5.3-5.1H5c0 3.41 2.72 6.23 6 6.72V20c0 .55.45 1 1 1s1-.45 1-1v-2.28c.91-.13 1.77-.45 2.54-.9L19.73 21 21 19.73 4.27 3z" />
    </svg>
  );
}

const STATE_LABELS: Record<string, string> = {
  disconnected: "Waiting…",
  connecting:   "Connecting…",
  initializing: "Getting ready…",
  listening:    "Listening",
  thinking:     "Thinking…",
  speaking:     "Speaking",
};

function AgentView({ recipeTitle, onEnd }: { recipeTitle: string; onEnd: () => void }) {
  const { state, audioTrack } = useVoiceAssistant();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const [agentHasSpoken, setAgentHasSpoken] = useState(false);

  useEffect(() => {
    if (state === "speaking") setAgentHasSpoken(true);
  }, [state]);

  const toggleMic = () => {
    localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
  };

  const label = STATE_LABELS[state] ?? state;

  // Pill gets a modifier class for speaking/listening so it glows differently
  const pillClass = `state-pill${
    state === "speaking" ? " state-pill--speaking" :
    state === "listening" ? " state-pill--listening" : ""
  }`;

  const micClass = `mic-btn ${isMicrophoneEnabled ? "mic-btn--live" : "mic-btn--muted"}`;

  return (
    <div className="session-page">
      <header className="session-header">
        <span className="session-wordmark">Suvai</span>
        <span className="session-recipe">{recipeTitle}</span>
        <span className={pillClass}>{label}</span>
      </header>

      <section className="visualizer-section">
        <div className="viz-container">
          <BarVisualizer
            state={state}
            trackRef={audioTrack}
            style={{ width: "100%", height: "100%" }}
          />
        </div>
        <p className="agent-hint">
          {!agentHasSpoken ? "Waiting for chef…" :
           state === "speaking" ? "Chef is talking…" :
           state === "listening" ? "Go ahead, I'm listening" :
           "Waiting for chef…"}
        </p>
      </section>

      <div className="session-controls">
        <button
          className={micClass}
          onClick={toggleMic}
          aria-label={isMicrophoneEnabled ? "Mute microphone" : "Unmute microphone"}
        >
          {isMicrophoneEnabled ? <MicIcon /> : <MicOffIcon />}
        </button>
        <p className="mic-hint">
          {isMicrophoneEnabled ? "Tap to mute" : "Tap to unmute"}
        </p>
        <button className="end-btn" onClick={onEnd}>
          End Session
        </button>
      </div>
    </div>
  );
}

export default function VoiceSession({ token, serverUrl, recipeTitle, onEnd }: Props) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onEnd}
    >
      <RoomAudioRenderer />
      <AgentView recipeTitle={recipeTitle} onEnd={onEnd} />
    </LiveKitRoom>
  );
}
