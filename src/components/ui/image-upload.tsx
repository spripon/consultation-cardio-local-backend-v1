import React, { useRef, useState } from 'react';
import { Button } from './button';
import { Card } from './card';
import { Upload, X, FileImage } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onImageRemove: () => void;
  selectedImage?: File | null;
  className?: string;
  disabled?: boolean;
}

export const ImageUpload = ({ 
  onImageSelect, 
  onImageRemove, 
  selectedImage, 
  className,
  disabled 
}: ImageUploadProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleFileSelect = (file: File) => {
    if (file.type.startsWith('image/')) {
      onImageSelect(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files);
    if (files[0]) {
      handleFileSelect(files[0]);
    }
  };

  return (
    <Card 
      className={cn(
        "border-2 border-dashed transition-colors cursor-pointer",
        dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25",
        selectedImage ? "border-solid border-primary" : "",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      onClick={!disabled ? handleClick : undefined}
      onDragOver={!disabled ? handleDragOver : undefined}
      onDragLeave={!disabled ? handleDragLeave : undefined}
      onDrop={!disabled ? handleDrop : undefined}
    >
      <div className="p-6">
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileSelect(file);
          }}
          disabled={disabled}
        />
        
        {selectedImage ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileImage className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium">{selectedImage.name}</span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  onImageRemove();
                }}
                disabled={disabled}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="text-xs text-muted-foreground">
              Cliquez pour changer l'image
            </div>
          </div>
        ) : (
          <div className="text-center space-y-4">
            <Upload className="h-12 w-12 mx-auto text-muted-foreground" />
            <div className="space-y-2">
              <p className="text-sm font-medium">
                Téléverser une photo du compte-rendu médical
              </p>
              <p className="text-xs text-muted-foreground">
                Glissez-déposez ou cliquez pour sélectionner
              </p>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};