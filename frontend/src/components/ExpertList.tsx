import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Building2, MapPin, GraduationCap, BookOpen, Link, Star } from "lucide-react"
import { Expert } from "@/lib/api"

/**
 * Props for the ExpertList component
 */
interface ExpertListProps {
  /** Source of experts to display ("linkedin" or "scholar") */
  source: "linkedin" | "scholar"
  /** Array of expert objects to display */
  experts: Expert[]
}

/**
 * Component that displays a list of experts with filtering and sorting
 * Features:
 * - Filters experts by source (LinkedIn/Google Scholar)
 * - Sorts Google Scholar experts by citations
 * - Displays expert details with conditional rendering
 * - Implements responsive card layout
 * 
 * @param source - Source of experts to display
 * @param experts - Array of expert objects
 */
export function ExpertList({ source, experts }: ExpertListProps) {
  // Filter experts based on source and sort by citations for scholar
  const filteredExperts = experts
    .filter(expert => expert.source === source)
    .sort((a, b) => source === "scholar" ? (b.citations || 0) - (a.citations || 0) : 0);

  // Show empty state if no experts found
  if (filteredExperts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No {source === "linkedin" ? "LinkedIn" : "Google Scholar"} experts found
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {filteredExperts.map((expert) => (
        <div 
          key={`${expert.name}-${expert.source}`}
          className="group relative flex items-start justify-between p-6 bg-white rounded-xl border border-gray-100 hover:shadow-lg hover:border-blue-100 transition-all duration-200"
        >
          {/* Expert Header Section */}
          <div className="space-y-3 flex-1 min-w-0">
            <div className="flex items-center gap-3">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 group-hover:text-blue-600 transition-colors">
                  {expert.name}
                </h3>
                <p className="text-gray-600">{expert.title}</p>
              </div>
            </div>
            
            {/* Expert Details Section */}
            {expert.source === "linkedin" ? (
              // LinkedIn Expert Details
              <div className="flex items-center gap-4 text-sm text-gray-500">
                {expert.company && (
                  <div className="flex items-center gap-1.5">
                    <Building2 className="h-4 w-4 text-blue-500" />
                    <span>{expert.company}</span>
                  </div>
                )}
                {expert.location && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-4 w-4 text-blue-500" />
                    <span>{expert.location}</span>
                  </div>
                )}
              </div>
            ) : (
              // Google Scholar Expert Details
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <div className="flex items-center gap-1.5">
                  <BookOpen className="h-4 w-4 text-purple-500" />
                  <span>{expert.citations || 0} citations</span>
                </div>
              </div>
            )}

            {/* Skills/Interests Section */}
            <div className="flex flex-wrap gap-2 pt-2">
              {(expert.source === "linkedin" ? expert.skills || [] : expert.interests || []).map((item) => (
                <Badge 
                  key={item} 
                  variant="secondary"
                  className={`${
                    expert.source === "linkedin"
                      ? "bg-blue-50 text-blue-600 hover:bg-blue-100"
                      : "bg-purple-50 text-purple-600 hover:bg-purple-100"
                  }`}
                >
                  {item}
                </Badge>
              ))}
            </div>
          </div>

          {/* Action Button */}
          <Button 
            variant="outline" 
            className={`ml-4 flex-shrink-0 self-start ${
              expert.source === "linkedin"
                ? "hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200"
                : "hover:bg-purple-50 hover:text-purple-600 hover:border-purple-200"
            } transition-colors`}
          >
            <Link className="h-4 w-4 mr-2" />
            View Profile
          </Button>
        </div>
      ))}
    </div>
  )
} 