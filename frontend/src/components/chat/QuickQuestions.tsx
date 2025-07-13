import { Button } from "@/components/ui/button";

interface QuickQuestionsProps {
  onQuestionSelect: (question: string) => void;
  disabled?: boolean;
}

const quickQuestions = [
  { display: "Rangkum Dokumen", template: "Rangkum isi dokumen [nama]" },
  {
    display: "Waktu Perjanjian",
    template: "Kapan pembuatan perjanjian dari dokumen [nama]",
  },
  {
    display: "Lahan Properti",
    template: "Luas lahan dan lokasi lahan properti dokumen [nama]",
  },
  {
    display: "Area Rambah",
    template: "Luas area dan lokasi area rambah dokumen [nama]",
  },
  {
    display: "Isi Pasal",
    template: "Rangkum isi pasal [Pasal] dari dokumen [nama]",
  },
];

export const QuickQuestions = ({
  onQuestionSelect,
  disabled = false,
}: QuickQuestionsProps) => {
  return (
    <div className="px-6 py-3 border-t border-border bg-background/50">
      <div className="flex flex-wrap gap-2 justify-center">
        {quickQuestions.map((questionObj) => (
          <Button
            key={questionObj.display}
            variant="outline"
            size="sm"
            onClick={() => onQuestionSelect(questionObj.template)}
            disabled={disabled}
            className="text-xs bg-secondary/50 hover:bg-secondary border-border text-muted-foreground hover:text-foreground transition-smooth"
          >
            {questionObj.display}
          </Button>
        ))}
      </div>
    </div>
  );
};
