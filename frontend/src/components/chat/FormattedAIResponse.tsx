import React from "react";
import {
  FormattedSection,
  parseAIResponse,
  cleanTextContent,
} from "@/utils/textFormatter";

interface FormattedAIResponseProps {
  text: string;
  className?: string;
}

export const FormattedAIResponse: React.FC<FormattedAIResponseProps> = ({
  text,
  className = "",
}) => {
  const sections = parseAIResponse(text);

  const renderSection = (section: FormattedSection, index: number) => {
    const baseClasses = "mb-4 last:mb-0";

    switch (section.type) {
      case "heading":
        const HeadingTag = `h${
          section.level || 2
        }` as keyof JSX.IntrinsicElements;
        const headingClasses = {
          1: "text-xl font-bold text-foreground mb-4 border-b border-border pb-2",
          2: "text-lg font-bold text-foreground mb-3",
          3: "text-base font-semibold text-foreground mb-2",
          4: "text-sm font-medium text-muted-foreground mb-2",
          5: "text-xs font-medium text-muted-foreground mb-1",
          6: "text-xs font-normal text-muted-foreground mb-1",
        };

        return (
          <HeadingTag
            key={index}
            className={`${headingClasses[section.level || 2]} ${baseClasses}`}
          >
            {cleanTextContent(section.content as string)}
          </HeadingTag>
        );

      case "list":
        return (
          <ul
            key={index}
            className={`list-disc list-outside space-y-2 text-sm text-foreground ml-4 pl-2 ${baseClasses}`}
          >
            {(section.content as string[]).map((item, itemIndex) => (
              <li key={itemIndex} className="leading-relaxed">
                {cleanTextContent(item)}
              </li>
            ))}
          </ul>
        );

      case "numbered-list":
        return (
          <ol
            key={index}
            className={`list-decimal list-outside space-y-2 text-sm text-foreground ml-4 pl-2 ${baseClasses}`}
          >
            {(section.content as string[]).map((item, itemIndex) => (
              <li key={itemIndex} className="leading-relaxed">
                {cleanTextContent(item)}
              </li>
            ))}
          </ol>
        );

      case "paragraph":
      default:
        return (
          <p
            key={index}
            className={`text-sm leading-relaxed text-foreground ${baseClasses}`}
          >
            {cleanTextContent(section.content as string)}
          </p>
        );
    }
  };

  // If no structured content found, return as formatted text
  if (sections.length === 0) {
    // Try to format raw text with better line breaks
    const formattedText = text
      .split("\n")
      .filter((line) => line.trim() !== "")
      .map((line) => line.trim())
      .join("\n");

    return (
      <div
        className={`ai-response-content text-sm leading-relaxed text-foreground whitespace-pre-line ${className}`}
      >
        {formattedText}
      </div>
    );
  }

  return (
    <div className={`ai-response-content space-y-3 ${className}`}>
      {sections.map((section, index) => renderSection(section, index))}
    </div>
  );
};
