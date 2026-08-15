import { Mic, MicOff, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useSpeechToText } from "@/hooks/useSpeechToText";

interface DictationButtonProps {
  onTranscript: (text: string) => void;
  size?: "sm" | "default" | "lg";
}

export const DictationButton = ({ onTranscript, size = "sm" }: DictationButtonProps) => {
  const { isListening, isProcessing, startListening, stopListening } = useSpeechToText({
    onTranscript,
  });

  const handleClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  return (
    <Button
      type="button"
      variant={isListening ? "destructive" : "outline"}
      size={size}
      onClick={handleClick}
      disabled={isProcessing}
      className="flex items-center gap-2"
    >
      {isProcessing ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : isListening ? (
        <MicOff className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
      {isListening ? "Arrêter" : "Dicter"}
    </Button>
  );
};