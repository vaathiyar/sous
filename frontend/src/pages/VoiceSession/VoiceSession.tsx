import '@/styles/VoiceSession.css';
import { LiveKitRoom, RoomAudioRenderer } from '@livekit/components-react';
import '@livekit/components-styles';
import { AgentView } from './AgentView';

interface VoiceSessionProps {
  token: string;
  serverUrl: string;
  recipeTitle: string;
  onEnd: () => void;
}

export default function VoiceSession({ token, serverUrl, recipeTitle, onEnd }: VoiceSessionProps) {
  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      audio={true}
      video={false}
      onDisconnected={onEnd}
    >
      <RoomAudioRenderer />
      <AgentView recipeTitle={recipeTitle} onEnd={onEnd} />
    </LiveKitRoom>
  );
}
