"use client"

import { ExpertList } from "./ExpertList"
import { Expert } from "@/lib/api"

/**
 * Props for the ExpertTabs component
 */
interface ExpertTabsProps {
  /** Array of expert results from the search */
  searchResults?: Expert[]
}

/**
 * Component that displays expert results in separate tabs for LinkedIn and Google Scholar
 * Features:
 * - Filters experts by source
 * - Displays expert count for each source
 * - Implements responsive grid layout
 * 
 * @param searchResults - Array of expert results to display
 */
export function ExpertTabs({ searchResults = [] }: ExpertTabsProps) {
  // Filter experts by source
  const linkedinExperts = searchResults.filter(e => e.source === "linkedin")
  const scholarExperts = searchResults.filter(e => e.source === "scholar")

  return (
    <div className="w-full">
      <div className="grid grid-cols-2 gap-6">
        {/* LinkedIn Experts Tab */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            LinkedIn Experts ({linkedinExperts.length})
          </h2>
          <ExpertList source="linkedin" experts={linkedinExperts} />
        </div>

        {/* Google Scholar Experts Tab */}
        <div>
          <h2 className="text-lg font-semibold text-gray-800 mb-4">
            Google Scholar Experts ({scholarExperts.length})
          </h2>
          <ExpertList source="scholar" experts={scholarExperts} />
        </div>
      </div>
    </div>
  )
} 