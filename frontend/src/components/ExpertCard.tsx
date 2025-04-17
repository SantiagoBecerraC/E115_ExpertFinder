import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Building2, MapPin, GraduationCap, BookOpen, Link } from "lucide-react"
import { CredibilityBadge } from "./CredibilityBadge"

interface Expert {
  id: string
  name: string
  title: string
  source: "linkedin" | "scholar"
  company?: string
  location?: string
  skills?: string[]
  citations?: number
  interests?: string[]
  publications?: number
  credibility_level?: number
  credibility_percentile?: number
  years_experience?: number
}

interface ExpertCardProps {
  expert: Expert
}

export function ExpertCard({ expert }: ExpertCardProps) {
  return (
    <Card className="h-full flex flex-col hover:shadow-md transition-shadow duration-200">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold text-gray-800">{expert.name}</CardTitle>
          {expert.source === "linkedin" && expert.credibility_level && (
            <CredibilityBadge 
              level={expert.credibility_level} 
              percentile={expert.credibility_percentile}
              yearsExperience={expert.years_experience}
            />
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        <div className="space-y-2">
          <p className="text-gray-600 font-medium">{expert.title}</p>
          {expert.source === "linkedin" ? (
            <>
              {expert.company && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Building2 className="h-4 w-4" />
                  <span>{expert.company}</span>
                </div>
              )}
              {expert.location && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <MapPin className="h-4 w-4" />
                  <span>{expert.location}</span>
                </div>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <GraduationCap className="h-4 w-4" />
                <span>{expert.publications} publications</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <BookOpen className="h-4 w-4" />
                <span>{expert.citations} citations</span>
              </div>
            </>
          )}
        </div>

        <div className="space-y-2">
          <h4 className="font-medium text-gray-700">
            {expert.source === "linkedin" ? "Skills" : "Research Interests"}
          </h4>
          <div className="flex flex-wrap gap-2">
            {(expert.source === "linkedin" ? expert.skills : expert.interests)?.map((item) => (
              <Badge 
                key={item} 
                variant="secondary"
                className="bg-blue-50 text-blue-600 hover:bg-blue-100"
              >
                {item}
              </Badge>
            ))}
          </div>
        </div>

        <div className="pt-4">
          <Button 
            variant="outline" 
            className="w-full hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200 transition-colors"
          >
            <Link className="h-4 w-4 mr-2" />
            View Profile
          </Button>
        </div>
      </CardContent>
    </Card>
  )
} 