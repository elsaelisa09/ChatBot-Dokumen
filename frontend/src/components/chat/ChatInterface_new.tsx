import { useState, useRef, useEffect } from "react";
import { ChatHeader } from "./ChatHeader";
import { ChatBubble } from "./ChatBubble";
import { ChatInput } from "./ChatInput";
import { UploadedFile } from "./UploadedFile";
import { QuickQuestions } from "./QuickQuestions";
import { useToast } from "@/hooks/use-toast";
import { Bot } from "lucide-react";
import { documentAIAPI } from "@/services/documentAI";

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: string;
}

interface UploadedFileInfo {
  name: string;
  file: File;
  uploadResponse?: any;
}

export const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFileInfo[]>([]);
  const [selectedQuestion, setSelectedQuestion] = useState("");
  const [isBackendConnected, setIsBackendConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Check backend connection on component mount
  useEffect(() => {
    checkBackendConnection();
  }, []);

  const checkBackendConnection = async () => {
    try {
      await documentAIAPI.healthCheck();
      setIsBackendConnected(true);
      console.log("Backend connected successfully");
    } catch (error) {
      setIsBackendConnected(false);
      console.error("Backend connection failed:", error);
      toast({
        title: "Backend Disconnected",
        description:
          "Cannot connect to DocumentAI backend. Please ensure backend is running.",
        variant: "destructive",
      });
    }
  };

  const handleSendMessage = async (messageText: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      isUser: true,
      timestamp: new Date().toLocaleTimeString("id-ID", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      if (!isBackendConnected) {
        throw new Error(
          "Backend tidak terhubung. Silakan pastikan server backend berjalan."
        );
      }

      // Call backend API
      const response = await documentAIAPI.askQuestion(messageText);

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isUser: false,
        timestamp: new Date().toLocaleTimeString("id-ID", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      console.error("Error asking question:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Maaf, terjadi kesalahan saat memproses pertanyaan Anda. ${
          error instanceof Error ? error.message : "Silakan coba lagi."
        }`,
        isUser: false,
        timestamp: new Date().toLocaleTimeString("id-ID", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, errorMessage]);

      toast({
        title: "Error",
        description: "Gagal mengirim pertanyaan ke server",
        variant: "destructive",
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    for (const file of Array.from(files)) {
      if (file.type === "application/pdf") {
        try {
          // Check if file already exists
          if (uploadedFiles.some((f) => f.name === file.name)) {
            toast({
              title: "File sudah ada",
              description: "File dengan nama yang sama sudah diupload",
              variant: "destructive",
            });
            continue;
          }

          // Show upload in progress
          toast({
            title: "Uploading...",
            description: `Mengunggah ${file.name}`,
          });

          // Upload to backend
          const uploadResponse = await documentAIAPI.uploadFile(file);

          // Add to uploaded files list
          setUploadedFiles((prev) => [
            ...prev,
            { name: file.name, file, uploadResponse },
          ]);

          toast({
            title: "File berhasil diunggah",
            description: `${file.name} telah diproses dan siap untuk ditanyakan`,
          });
        } catch (error) {
          console.error("Upload failed:", error);
          toast({
            title: "Upload gagal",
            description: `Gagal mengunggah ${file.name}. ${
              error instanceof Error ? error.message : "Silakan coba lagi."
            }`,
            variant: "destructive",
          });
        }
      } else {
        toast({
          title: "Format file tidak didukung",
          description: "Hanya file PDF yang dapat diunggah",
          variant: "destructive",
        });
      }
    }
  };

  const handleRemoveFile = async (fileName: string) => {
    try {
      // Find the file info
      const fileInfo = uploadedFiles.find((f) => f.name === fileName);

      if (fileInfo?.uploadResponse?.filename) {
        // Delete from backend
        await documentAIAPI.deleteFile(fileInfo.uploadResponse.filename);
      }

      // Remove from local state
      setUploadedFiles((prev) => prev.filter((f) => f.name !== fileName));

      toast({
        title: "File dihapus",
        description: "Dokumen telah dihapus dari sistem",
      });
    } catch (error) {
      console.error("Failed to delete file:", error);
      toast({
        title: "Gagal menghapus",
        description: "Terjadi kesalahan saat menghapus file",
        variant: "destructive",
      });
    }
  };

  const handleVoiceInput = (voiceText: string) => {
    if (voiceText.trim()) {
      handleSendMessage(voiceText.trim());
    }
  };

  const handleQuestionSelect = (question: string) => {
    setSelectedQuestion(question);
  };

  // Clear selected question after it's used
  const handleSendMessageWithClear = (messageText: string) => {
    handleSendMessage(messageText);
    setSelectedQuestion(""); // Clear the selected question after sending
  };

  return (
    <div className="max-w-2xl mx-auto h-[calc(100vh-2rem)] bg-chat-area-bg flex flex-col border border-border rounded-lg shadow-lg">
      <ChatHeader />

      {/* Backend connection status */}
      {!isBackendConnected && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mx-4 mt-2">
          <strong>Warning:</strong> Backend tidak terhubung. Pastikan server
          backend berjalan di http://localhost:8000
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {uploadedFiles.length > 0 && (
          <div className="space-y-2">
            {uploadedFiles.map((file) => (
              <UploadedFile
                key={file.name}
                fileName={file.name}
                onRemove={() => handleRemoveFile(file.name)}
              />
            ))}
          </div>
        )}

        {messages.length === 0 && uploadedFiles.length === 0 && (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-3xl bg-foreground flex items-center justify-center mx-auto mb-6">
              <Bot className="w-10 h-10 text-background" />
            </div>
            <h3 className="text-3xl font-bold text-foreground mb-3">AIDocs</h3>
            <p className="text-muted-foreground text-sm">
              Tanya Jawab Seputar Dokumen Kamu!
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Backend Status:{" "}
              {isBackendConnected ? "🟢 Connected" : "🔴 Disconnected"}
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatBubble
            key={message.id}
            message={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
          />
        ))}

        {isTyping && (
          <ChatBubble
            message="Sedang mengetik..."
            isUser={false}
            timestamp=""
            isTyping={true}
          />
        )}

        <div ref={messagesEndRef} />
      </div>

      {messages.length === 0 && (
        <div className="px-6">
          <QuickQuestions onQuestionSelect={handleQuestionSelect} />
        </div>
      )}

      <div className="border-t border-border p-6">
        <ChatInput
          onSendMessage={handleSendMessageWithClear}
          onFileUpload={handleFileUpload}
          onVoiceInput={handleVoiceInput}
          selectedQuestion={selectedQuestion}
          isDisabled={!isBackendConnected}
        />
      </div>
    </div>
  );
};
