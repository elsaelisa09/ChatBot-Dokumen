/**
 * Utility functions for formatting AI responses
 */

export interface FormattedSection {
  type: "heading" | "paragraph" | "list" | "numbered-list";
  content: string | string[];
  level?: number; // For headings (1-6)
}

/**
 * Parse and format AI response text into structured sections
 */
export function parseAIResponse(text: string): FormattedSection[] {
  const sections: FormattedSection[] = [];

  // Pre-process text to normalize line breaks and spacing
  const normalizedText = text
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  // Split by double line breaks to identify paragraphs
  const paragraphs = normalizedText
    .split(/\n\n+/)
    .filter((p) => p.trim() !== "");

  for (const paragraph of paragraphs) {
    const lines = paragraph
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line !== "");

    // Check for headings with bold formatting
    const firstLine = lines[0];
    if (firstLine && /^\*\*(.+?)\*\*/.test(firstLine)) {
      const match = firstLine.match(/^\*\*(.+?)\*\*/);
      if (match) {
        sections.push({
          type: "heading",
          content: match[1].trim(),
          level: 2,
        });

        // Process remaining lines in this paragraph
        const remainingLines = lines.slice(1);
        if (remainingLines.length > 0) {
          const remainingText = remainingLines.join(" ").trim();
          if (remainingText) {
            sections.push({
              type: "paragraph",
              content: remainingText,
            });
          }
        }
        continue;
      }
    }

    // Check if this paragraph contains bullet points
    const hasBulletPoints = lines.some((line) => /^[-•*]\s+/.test(line));
    if (hasBulletPoints) {
      const listItems: string[] = [];
      let introText = "";

      for (const line of lines) {
        if (/^[-•*]\s+/.test(line)) {
          listItems.push(line.replace(/^[-•*]\s+/, "").trim());
        } else if (listItems.length === 0) {
          // This is intro text before list items
          introText += (introText ? " " : "") + line;
        }
      }

      // Add intro text if exists
      if (introText.trim()) {
        sections.push({
          type: "paragraph",
          content: introText.trim(),
        });
      }

      // Add list items
      if (listItems.length > 0) {
        sections.push({
          type: "list",
          content: listItems,
        });
      }
      continue;
    }

    // Check for numbered lists
    const hasNumberedList = lines.some((line) => /^\d+\.\s+/.test(line));
    if (hasNumberedList) {
      const listItems: string[] = [];
      let introText = "";

      for (const line of lines) {
        if (/^\d+\.\s+/.test(line)) {
          listItems.push(line.replace(/^\d+\.\s+/, "").trim());
        } else if (listItems.length === 0) {
          introText += (introText ? " " : "") + line;
        }
      }

      if (introText.trim()) {
        sections.push({
          type: "paragraph",
          content: introText.trim(),
        });
      }

      if (listItems.length > 0) {
        sections.push({
          type: "numbered-list",
          content: listItems,
        });
      }
      continue;
    }

    // Regular paragraph - join all lines
    const paragraphText = lines.join(" ").trim();
    if (paragraphText) {
      sections.push({
        type: "paragraph",
        content: paragraphText,
      });
    }
  }

  return sections;
}

/**
 * Clean and format text content
 */
export function cleanTextContent(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, "$1") // Remove bold markdown
    .replace(/\*(.+?)\*/g, "$1") // Remove italic markdown
    .replace(/\s{2,}/g, " ") // Replace multiple spaces with single space
    .replace(/\n\s*\n/g, "\n") // Clean up multiple line breaks
    .trim();
}
