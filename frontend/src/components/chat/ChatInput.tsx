import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Paperclip, Mic, MicOff, Send } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/hooks/use-toast";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onFileUpload?: (files: FileList) => void;
  onVoiceInput?: (voiceText: string) => void;
  disabled?: boolean;
  placeholder?: string;
  selectedQuestion?: string;
  isDisabled?: boolean;
}

export const ChatInput = ({
  onSendMessage,
  onFileUpload,
  onVoiceInput,
  disabled = false,
  placeholder = "Ketik pertanyaan Anda...",
  selectedQuestion = "",
  isDisabled = false,
}: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (selectedQuestion) {
      setMessage(selectedQuestion);
    }
  }, [selectedQuestion]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isDisabled) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0 && onFileUpload) {
      onFileUpload(files);
    }
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Temporarily disable speech recognition to avoid compatibility issues
  const toggleRecording = async () => {
    toast({
      title: "Feature tidak tersedia",
      description: "Fitur speech recognition sementara dinonaktifkan.",
      variant: "destructive",
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="flex items-center gap-2 p-3 bg-background border border-border rounded-lg focus-within:ring-2 focus-within:ring-ring focus-within:border-transparent">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="p-2 hover:bg-accent"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled || isDisabled}
        >
          <Paperclip className="w-4 h-4" />
        </Button>

        <Input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
          multiple
        />

        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          disabled={disabled || isDisabled}
          className="flex-1 border-0 bg-transparent focus-visible:ring-0 focus-visible:ring-offset-0"
        />

        <Button
          type="button"
          variant="ghost"
          size="sm"
          className={cn(
            "p-2 hover:bg-accent",
            isRecording && "bg-red-100 text-red-600 hover:bg-red-200"
          )}
          onClick={toggleRecording}
          disabled={disabled || isDisabled}
        >
          {isRecording ? (
            <MicOff className="w-4 h-4" />
          ) : (
            <Mic className="w-4 h-4" />
          )}
        </Button>

        <Button
          type="submit"
          size="sm"
          disabled={!message.trim() || disabled || isDisabled}
          className="px-4"
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      {isDisabled && (
        <p className="text-sm text-red-600 text-center">
          Backend tidak terhubung. Pastikan server backend berjalan.
        </p>
      )}
    </form>
  );
};
