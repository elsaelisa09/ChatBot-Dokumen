import { FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface UploadedFileProps {
  fileName: string;
  onRemove: () => void;
}

export const UploadedFile = ({ fileName, onRemove }: UploadedFileProps) => {
  return (
    <div className="flex items-center gap-2 bg-secondary rounded-lg p-3 mb-4">
      <div className="w-8 h-8 rounded bg-destructive/20 flex items-center justify-center">
        <FileText className="w-4 h-4 text-destructive" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          {fileName}
        </p>
      </div>
      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="text-muted-foreground hover:text-foreground"
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
};