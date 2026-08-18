interface ChatMarkdownProps {
  content: string;
}

export function ChatMarkdown({ content }: ChatMarkdownProps) {
  const blocks = content.split(/\n{2,}/);

  return (
    <div className="space-y-2">
      {blocks.map((block, index) => {
        const lines = block.split("\n").filter(Boolean);
        const isList = lines.every((line) => /^[-*]\s+/.test(line.trim()));

        if (isList) {
          return (
            <ul key={`${block}-${index}`} className="list-disc space-y-1 pl-5">
              {lines.map((line) => (
                <li key={line}>{renderInlineMarkdown(line.replace(/^[-*]\s+/, ""))}</li>
              ))}
            </ul>
          );
        }

        return (
          <p key={`${block}-${index}`} className="leading-relaxed">
            {renderInlineMarkdown(block)}
          </p>
        );
      })}
    </div>
  );
}

function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).filter(Boolean);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={`${part}-${index}`}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={`${part}-${index}`} className="rounded bg-slate-100 px-1 py-0.5 text-[0.8em] text-slate-950">
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={`${part}-${index}`}>{part}</span>;
  });
}
