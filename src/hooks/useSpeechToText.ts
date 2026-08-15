import { useState, useRef, useCallback } from 'react';
import { toast } from 'sonner';

interface SpeechToTextOptions {
  onTranscript: (text: string) => void;
  apiKey?: string;
}

export const useSpeechToText = ({ onTranscript, apiKey }: SpeechToTextOptions) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const transcribeWithWhisper = useCallback(async (audioBlob: Blob) => {
    console.log('🎤 Début transcription avec Whisper, taille audio:', audioBlob.size, 'bytes');
    
    if (!apiKey) {
      console.error('❌ Clé API OpenAI manquante');
      toast.error("Clé API OpenAI manquante");
      return;
    }

    try {
      const formData = new FormData();
      // Utiliser l'extension appropriée selon le type MIME
      const extension = audioBlob.type.includes('wav') ? 'audio.wav' : 
                       audioBlob.type.includes('mp4') ? 'audio.mp4' : 'audio.webm';
      formData.append('file', audioBlob, extension);
      formData.append('model', 'whisper-1');
      formData.append('language', 'fr');
      
      console.log('📡 Envoi requête à Whisper API...');
      
      const response = await fetch('https://api.openai.com/v1/audio/transcriptions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${apiKey}`,
        },
        body: formData
      });

      console.log('📡 Réponse API reçue, status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ Erreur API Whisper:', response.status, errorText);
        throw new Error(`Erreur API: ${response.status} - ${errorText}`);
      }

      const data = await response.json();
      console.log('✅ Données reçues de Whisper:', data);
      
      if (data.text) {
        console.log('📝 Transcription:', data.text);
        onTranscript(data.text.trim());
        toast.success("Transcription réussie!");
      } else {
        console.warn('⚠️ Pas de texte dans la réponse');
        toast.warning("Aucun texte détecté dans l'audio");
      }
    } catch (error) {
      console.error('❌ Erreur transcription Whisper:', error);
      const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
      toast.error(`Erreur Whisper: ${errorMessage}`);
    }
  }, [apiKey, onTranscript]);

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
        
        console.log('📁 Blob audio créé:', audioBlob.size, 'bytes, type:', audioBlob.type);
        
        // Arrêter le stream
        stream.getTracks().forEach(track => track.stop());
        
        if (audioBlob.size === 0) {
          console.warn('⚠️ Audio vide, pas de transcription');
          toast.warning("Aucun audio enregistré");
          setIsListening(false);
          return;
        }
        
        // Transcrire avec Whisper
        setIsProcessing(true);
        await transcribeWithWhisper(audioBlob);
        setIsProcessing(false);
        setIsListening(false);
      };

      mediaRecorder.onerror = (event) => {
        console.error('Erreur MediaRecorder:', event);
        toast.error("Erreur lors de l'enregistrement audio");
        setIsListening(false);
        setIsProcessing(false);
      };

      // Démarrer l'enregistrement
      mediaRecorder.start(1000); // Collecter les données toutes les secondes
      setIsListening(true);
      toast.success("Enregistrement en cours... Parlez maintenant");
      
    } catch (error) {
      console.error('Erreur accès microphone:', error);
      toast.error("Impossible d'accéder au microphone");
    }
  }, [transcribeWithWhisper]);

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