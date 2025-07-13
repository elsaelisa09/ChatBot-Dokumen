import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import { FormattedAIResponse } from "./FormattedAIResponse";

interface ChatBubbleProps {
  message: string;
  isUser: boolean;
  timestamp?: string;
  isTyping?: boolean;
}

export const ChatBubble = ({
  message,
  isUser,
  timestamp,
  isTyping,
}: ChatBubbleProps) => {
  return (
    <div
      className={cn(
        "flex gap-3 mb-4 transition-smooth",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
            <Bot className="w-5 h-5 text-primary-foreground" />
          </div>
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3 transition-smooth",
          isUser
            ? "bg-chat-bubble-user text-primary-foreground rounded-br-md"
            : "bg-chat-bubble-ai text-foreground rounded-bl-md"
        )}
      >
        {isTyping ? (
          <div className="flex items-center gap-1">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-typing"></div>
              <div
                className="w-2 h-2 bg-muted-foreground rounded-full animate-typing"
                style={{ animationDelay: "0.2s" }}
              ></div>
              <div
                className="w-2 h-2 bg-muted-foreground rounded-full animate-typing"
                style={{ animationDelay: "0.4s" }}
              ></div>
            </div>
          </div>
        ) : (
          <div>
            {isUser ? (
              <p className="text-sm leading-relaxed">{message}</p>
            ) : (
              <FormattedAIResponse text={message} />
            )}
          </div>
        )}

        {timestamp && !isTyping && (
          <div className="mt-2 text-xs opacity-70">{timestamp}</div>
        )}
      </div>

      {isUser && (
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
            <User className="w-5 h-5 text-secondary-foreground" />
          </div>
        </div>
      )}
    </div>
  );
};
