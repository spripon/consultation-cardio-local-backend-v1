import { useState, useRef, useCallback } from "react";
import { toast } from "sonner";
import { postFormData } from "@/lib/apiClient";

interface SpeechToTextOptions {
  onTranscript: (text: string) => void;
}

export const useSpeechToText = ({ onTranscript }: SpeechToTextOptions) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const transcribeLocally = useCallback(async (audioBlob: Blob) => {
    // Aucun contenu patient n'est journalisé : uniquement des métadonnées techniques.
    try {
      const formData = new FormData();
      const extension = audioBlob.type.includes("wav")
        ? "audio.wav"
        : audioBlob.type.includes("mp4")
          ? "audio.mp4"
          : "audio.webm";
      formData.append("audio", audioBlob, extension);

      const data = await postFormData<{ text: string }>("/v1/transcribe", formData);

      if (data.text?.trim()) {
        onTranscript(data.text.trim());
        toast.success("Transcription réussie!");
      } else {
        toast.warning("Aucun texte détecté dans l'audio");
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Service de dictée locale indisponible";
      // Fail-closed : aucun repli vers un service de transcription externe.
      toast.error(`Transcription locale impossible : ${errorMessage}`);
    }
  }, [onTranscript]);

  const startListening = useCallback(async () => {
    try {
      console.log('🎤 Demande d\'accès au microphone...');
      
      // Demander la permission d'accéder au microphone
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        }
      });
      
      console.log('✅ Accès microphone accordé');
      
      // Réinitialiser les chunks audio
      audioChunksRef.current = [];
      
      // Créer le MediaRecorder avec un format plus compatible
      let mimeType = 'audio/wav';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/mp4';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = 'audio/webm';
        }
      }
      
      console.log('🎵 Format audio utilisé:', mimeType);
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log('🛑 Arrêt de l\'enregistrement, chunks:', audioChunksRef.current.length);
        
        // Créer le blob audio final avec le bon type MIME
      const audioBlob = new Blob(audioChunksRef.current, { 
          type: mimeType 
        });

        // Arrêter le stream
        stream.getTracks().forEach(track => track.stop());
        
        if (audioBlob.size === 0) {
          console.warn('⚠️ Audio vide, pas de transcription');
          toast.warning("Aucun audio enregistré");
          setIsListening(false);
          return;
        }
        
        // Transcrire avec le serveur local
        setIsProcessing(true);
        await transcribeLocally(audioBlob);
        setIsProcessing(false);
        setIsListening(false);
      };

      mediaRecorder.onerror = (event) => {
        console.error("Erreur MediaRecorder:", event);
        toast.error("Erreur lors de l'enregistrement audio");
        setIsListening(false);
        setIsProcessing(false);
      };

      // Démarrer l'enregistrement
      mediaRecorder.start(1000); // Collecter les données toutes les secondes
      setIsListening(true);
      toast.success("Enregistrement en cours... Parlez maintenant");
    } catch (error) {
      console.error("Erreur accès microphone:", error);
      toast.error("Impossible d'accéder au microphone");
    }
  }, [transcribeLocally]);

  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  return {
    isListening,
    isProcessing,
    startListening,
    stopListening,
  };
};