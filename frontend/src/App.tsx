import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <div className="min-h-screen bg-background p-4 relative">
        <Toaster />
        <Sonner />

        {/* PHR Logo - Bottom Right */}
        <div className="fixed bottom-4 right-4 z-10">
          <img
            src="/phr.png"
            alt="Pertamina Hulu Rokan"
            className="h-60 w-auto opacity-80 hover:opacity-100 transition-opacity"
          />
        </div>

        {/* PHR Logo - Bottom Left (Mirrored) */}
        <div className="fixed bottom-4 left-4 z-10">
          <img
            src="/phr.png"
            alt="Pertamina Hulu Rokan"
            className="h-60 w-auto opacity-80 hover:opacity-100 transition-opacity transform scale-x-[-1]"
          />
        </div>

        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </div>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
