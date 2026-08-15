import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Eye, EyeOff, Bot } from "lucide-react";

interface ApiKeyInputProps {
  openAIApiKey: string;
  onOpenAIApiKeyChange: (key: string) => void;
}

export const ApiKeyInput = ({ 
  openAIApiKey,
  onOpenAIApiKeyChange 
}: ApiKeyInputProps) => {
  const [showOpenAIKey, setShowOpenAIKey] = useState(false);

  return (
    <div className="space-y-4 mb-6">
      <Card className="p-4 bg-blue-50 border-blue-200 w-full">
        <div className="space-y-3">
          <div className="flex items-center space-x-2">
            <Bot className="h-4 w-4 text-blue-600" />
            <Label htmlFor="openai-api-key" className="text-sm font-medium text-blue-800">
              Clé API OpenAI (pour la dictée vocale Whisper)
            </Label>
          </div>
          <div className="flex gap-2 w-full">
            <div className="relative flex-1 min-w-0">
              <Input
                id="openai-api-key"
                type={showOpenAIKey ? "text" : "password"}
                value={openAIApiKey}
                onChange={(e) => onOpenAIApiKeyChange(e.target.value)}
                placeholder="Entrez votre clé API OpenAI..."
                className="pr-12 w-full"
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0 hover:bg-medical-100"
                onClick={() => setShowOpenAIKey(!showOpenAIKey)}
              >
                {showOpenAIKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <p className="text-xs text-blue-600">
            Permet la transcription vocale automatique avec Whisper et l'extraction de texte depuis une photo.
          </p>
        </div>
      </Card>
    </div>
  );
};