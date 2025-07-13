import { Bot } from "lucide-react";

export const ChatHeader = () => {
  return (
    <div className="border-b border-border bg-background px-6 py-2">
      <div className="flex items-center justify-between">
        {/* Left side - Document AI Chat with Bot icon */}
        <div className="flex items-center gap-2">
          <Bot className="w-6 h-6 text-foreground" />
          <h1 className="text-lg font-semibold text-foreground">
            Document AI Chat
          </h1>
        </div>

        {/* Right side - PHR Logo */}
        <div className="flex items-center">
          <img
            src="/logophr.png"
            alt="Pertamina Hulu Rokan"
            className="h-10 w-auto"
          />
        </div>
      </div>
    </div>
  );
};
