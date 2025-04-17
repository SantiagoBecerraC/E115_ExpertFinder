import React from "react";
import { Star } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface CredibilityBadgeProps {
  level: number;
  percentile?: number;
  yearsExperience?: number;
}

export function CredibilityBadge({ level, percentile, yearsExperience }: CredibilityBadgeProps) {
  // Define colors for different credibility levels
  const getColorByLevel = (level: number) => {
    switch (level) {
      case 5: return "bg-purple-100 text-purple-700 border-purple-300";
      case 4: return "bg-blue-100 text-blue-700 border-blue-300";
      case 3: return "bg-green-100 text-green-700 border-green-300";
      case 2: return "bg-yellow-100 text-yellow-700 border-yellow-300";
      case 1: 
      default: return "bg-gray-100 text-gray-700 border-gray-300";
    }
  };

  // Get appropriate colors based on level
  const colorClasses = getColorByLevel(level);

  // Format the tooltip content
  const tooltipContent = () => {
    let content = `Credibility Level: ${level}/5`;
    
    if (percentile !== undefined) {
      content += ` (${percentile.toFixed(1)}th percentile)`;
    }
    
    if (yearsExperience !== undefined) {
      content += `\nYears of Experience: ${yearsExperience}`;
    }
    
    return content;
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`flex items-center justify-center w-8 h-8 rounded-full ${colorClasses} border-2 font-bold shadow-sm hover:shadow transition-shadow cursor-help`}>
            {level}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-sm whitespace-pre-line">{tooltipContent()}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
} 