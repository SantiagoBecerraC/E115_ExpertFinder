/**
 * Main application page component that handles expert search and display
 * Features:
 * - Real-time search with API integration
 * - Chat history display
 * - Feature showcase
 * - Expert results display with tabs
 */
"use client"

import { SearchInput } from "@/components/ui/search-input"
import { ChatHistoryItem } from "@/components/ui/chat-history-item"
import { ExpertTabs } from "@/components/ExpertTabs"
import Image from "next/image"
import { useState } from "react"
import { Expert } from "../lib/api"

export default function Home() {
  // State for managing search results and loading state
  const [searchResults, setSearchResults] = useState<Expert[]>([])
  const [isSearching, setIsSearching] = useState(false)

  /**
   * Handles the search functionality by making an API call to the backend
   * and combining results with mock LinkedIn data
   * @param query - The search query string
   */
  const handleSearch = async (query: string) => {
    setIsSearching(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          max_results: 5,
        }),
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      setSearchResults(data.experts || [])
    } catch (error) {
      console.error('Error searching experts:', error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Mock chat history data for demonstration
  const chatHistory = [
    {
      id: 1,
      title: "Machine Learning Expert Search",
      timestamp: "2 hours ago",
      preview: "Looking for experts in deep learning and neural networks...",
      expertCount: 5
    },
    {
      id: 2,
      title: "Data Science Consultation",
      timestamp: "Yesterday",
      preview: "Need expertise in data analysis and visualization...",
      expertCount: 3
    },
    {
      id: 3,
      title: "AI Research Expert",
      timestamp: "2 days ago",
      preview: "Seeking specialists in reinforcement learning...",
      expertCount: 4
    }
  ]

  // Feature cards data for the landing page
  const features = [
    {
      icon: "🎯",
      title: "Precise Matching",
      description: "Find exactly the expertise you need in Computer Science and Life Sciences"
    },
    {
      icon: "🤝",
      title: "Bridge the Gap",
      description: "Connect with qualified experts who can help with your specific needs"
    },
    {
      icon: "💡",
      title: "Specialized Knowledge",
      description: "Access deep expertise across various technical and scientific domains"
    }
  ]

  return (
    <div className="flex h-screen bg-white">
      {/* Left Sidebar - Chat History */}
      <div className="w-80 border-r border-gray-200 flex flex-col bg-gray-50">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200 bg-white">
          <h2 className="text-xl font-semibold text-gray-800">Recent Searches</h2>
          <p className="text-sm text-gray-500 mt-1">Your previous expert searches</p>
        </div>

        {/* Chat History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {chatHistory.map((chat) => (
            <ChatHistoryItem
              key={chat.id}
              title={chat.title}
              timestamp={chat.timestamp}
              preview={chat.preview}
              expertCount={chat.expertCount}
              isActive={chat.id === 1}
            />
          ))}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <button className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear History
          </button>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-screen overflow-y-auto">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white">
          <div className="container mx-auto px-4 py-4">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 relative">
                <Image
                  src="/logo.svg"
                  alt="Expert Finder Logo"
                  width={64}
                  height={64}
                  priority
                />
              </div>
              <h1 className="text-3xl font-bold">EXPERT FINDER</h1>
            </div>
          </div>
        </header>

        {/* Description Section */}
        <div className="border-b border-gray-200 bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4 py-8">
            <div className="max-w-4xl mx-auto space-y-8">
              <div className="text-center space-y-4">
                <h2 className="text-2xl font-semibold text-gray-800">
                  Welcome to Expert Finder
                </h2>
                <p className="text-gray-600 max-w-2xl mx-auto">
                  Your bridge to expertise in Computer Science and Life Sciences
                </p>
              </div>

              {/* Search Input */}
              <div className="flex justify-center">
                <SearchInput onSearch={handleSearch} isLoading={isSearching} />
              </div>

              {/* Feature Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                {features.map((feature, index) => (
                  <div 
                    key={index}
                    className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
                  >
                    <div className="text-4xl mb-4">{feature.icon}</div>
                    <h3 className="text-lg font-semibold text-gray-800 mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600">
                      {feature.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results Container */}
        <div className="flex-1 bg-gradient-to-b from-gray-50 to-white">
          <div className="container mx-auto px-4 py-8">
            <div className="max-w-5xl mx-auto">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-semibold text-gray-800">Expert Results</h3>
                    <p className="text-gray-500 mt-1">Find and connect with domain experts</p>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <span className="px-3 py-1 bg-blue-50 text-blue-600 rounded-full">
                      {searchResults.length} Experts Found
                    </span>
                  </div>
                </div>
                <ExpertTabs searchResults={searchResults} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
