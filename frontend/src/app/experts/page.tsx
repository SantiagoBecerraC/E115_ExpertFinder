"use client"

import { ExpertTabs } from "@/components/ExpertTabs"

// Sample data for testing
const sampleExperts = [
  {
    id: "1",
    name: "John Doe",
    title: "Senior Software Engineer",
    source: "linkedin" as const,
    company: "Google",
    location: "Mountain View, CA",
    skills: ["React", "TypeScript", "Node.js", "AWS"],
  },
  {
    id: "2",
    name: "Jane Smith",
    title: "Research Scientist",
    source: "scholar" as const,
    citations: 1500,
    interests: ["Machine Learning", "Computer Vision", "Deep Learning"],
    publications: 25,
  },
  {
    id: "3",
    name: "Alex Johnson",
    title: "Data Science Lead",
    source: "linkedin" as const,
    company: "Microsoft",
    location: "Seattle, WA",
    skills: ["Python", "TensorFlow", "PyTorch", "Data Analysis"],
  },
  {
    id: "4",
    name: "Sarah Wilson",
    title: "Professor of Computer Science",
    source: "scholar" as const,
    citations: 3000,
    interests: ["Natural Language Processing", "AI Ethics", "Neural Networks"],
    publications: 45,
  },
]

export default function ExpertsPage() {
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Find Experts</h1>
      <ExpertTabs />
    </div>
  )
} 