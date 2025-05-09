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
import { useState, useEffect } from "react"
import { Expert } from "../lib/api"

// Interface for search history items
interface SearchHistoryItem {
  id: number;
  title: string;
  timestamp: string;
  preview: string;
  expertCount: number;
  query: string;
  searchCount: number; // Number of times this search has been performed
}

export default function Home() {
  // State for managing search results and loading state
  const [searchResults, setSearchResults] = useState<Expert[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([])
  const [activeSearchId, setActiveSearchId] = useState<number | null>(null)
  const [currentQuery, setCurrentQuery] = useState<string>("")

  /**
   * Load search history from localStorage on component mount
   */
  useEffect(() => {
    const storedHistory = localStorage.getItem('expertFinderSearchHistory')
    if (storedHistory) {
      try {
        const parsedHistory = JSON.parse(storedHistory)
        setSearchHistory(parsedHistory)
        // Set the most recent search as active if it exists
        if (parsedHistory.length > 0) {
          setActiveSearchId(parsedHistory[0].id)
        }
      } catch (error) {
        console.error('Error loading search history:', error)
      }
    }
  }, [])

  /**
   * Formats a date as a relative time string (e.g., "2 hours ago")
   */
  const getRelativeTimeString = (date: Date): string => {
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`
    return `${Math.floor(diffInSeconds / 604800)} weeks ago`
  }

  /**
   * Saves a search to history and localStorage
   * If the search already exists, updates its timestamp and increments its count
   */
  const saveSearchToHistory = (query: string, expertResults: Expert[]) => {
    // Check if this search query already exists in history
    const existingSearchIndex = searchHistory.findIndex(
      item => item.query.toLowerCase() === query.toLowerCase()
    );
    
    let updatedHistory: SearchHistoryItem[];
    
    if (existingSearchIndex !== -1) {
      // If this search already exists, update it
      const existingSearch = searchHistory[existingSearchIndex];
      const updatedSearch: SearchHistoryItem = {
        ...existingSearch,
        timestamp: getRelativeTimeString(new Date()),
        expertCount: expertResults.length,
        searchCount: existingSearch.searchCount + 1
      };
      
      // Create new array with the updated search moved to the top
      updatedHistory = [
        updatedSearch,
        ...searchHistory.slice(0, existingSearchIndex),
        ...searchHistory.slice(existingSearchIndex + 1)
      ];
      
      setActiveSearchId(existingSearch.id);
    } else {
      // Create a new search entry
      const newSearch: SearchHistoryItem = {
        id: Date.now(),
        title: query,
        timestamp: getRelativeTimeString(new Date()),
        preview: `Search for experts in ${query}...`,
        expertCount: expertResults.length,
        query: query,
        searchCount: 1
      };
      
      // Add the new search to the top of history
      updatedHistory = [newSearch, ...searchHistory.slice(0, 9)]; // Keep only the 10 most recent searches
      setActiveSearchId(newSearch.id);
    }
    
    // Update state and localStorage
    setSearchHistory(updatedHistory);
    localStorage.setItem('expertFinderSearchHistory', JSON.stringify(updatedHistory));
  }

  /**
   * Handles the search functionality by making an API call to the backend
   * and combining results with mock LinkedIn data
   * @param query - The search query string
   */
  const handleSearch = async (query: string) => {
    setIsSearching(true)
    setCurrentQuery(query)
    try {
      // Set API URL - handle both absolute URLs and relative paths
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || '/backend';
      
      // Construct the full URL properly, handling relative paths
      const searchUrl = apiUrl.startsWith('http') 
        ? `${apiUrl}/search`                     // If it's a full URL (starts with http)
        : `${apiUrl.endsWith('/') ? apiUrl.slice(0, -1) : apiUrl}/search`;  // If it's a path like '/backend'
      
      const response = await fetch(searchUrl, {
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
      const experts = data.experts || []
      setSearchResults(experts)
      
      // Save this search to history
      saveSearchToHistory(query, experts)
    } catch (error) {
      console.error('Error searching experts:', error)
      setSearchResults([])
      
      // Fallback to mock data for demonstration when backend is unavailable
      if (!searchHistory.length) {
        // Only create a mock entry if history is empty
        const mockExperts: Expert[] = [
          { 
            id: "mock1", 
            name: "Demo Expert", 
            title: "AI Researcher", 
            source: "linkedin" as const
          }
        ];
        saveSearchToHistory(query, mockExperts);
      }
    } finally {
      setIsSearching(false)
    }
  }

  /**
   * Deletes a specific search history item
   */
  const deleteSearchHistoryItem = (id: number) => {
    const updatedHistory = searchHistory.filter(item => item.id !== id)
    setSearchHistory(updatedHistory)
    
    // If the active item was deleted, set the most recent as active (if any)
    if (activeSearchId === id && updatedHistory.length > 0) {
      setActiveSearchId(updatedHistory[0].id)
    } else if (updatedHistory.length === 0) {
      setActiveSearchId(null)
    }
    
    localStorage.setItem('expertFinderSearchHistory', JSON.stringify(updatedHistory))
  }

  /**
   * Clears search history from state and localStorage
   */
  const clearSearchHistory = () => {
    setSearchHistory([])
    setActiveSearchId(null)
    localStorage.removeItem('expertFinderSearchHistory')
  }

  /**
   * Handles clicking on a search history item
   */
  const handleSearchHistoryClick = (item: SearchHistoryItem) => {
    setActiveSearchId(item.id)
    setCurrentQuery(item.query)
    handleSearch(item.query)
  }

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
          {searchHistory.length > 0 ? (
            searchHistory.map((item) => (
              <ChatHistoryItem
                key={item.id}
                title={item.title}
                timestamp={item.timestamp}
                preview={item.preview}
                expertCount={item.expertCount}
                isActive={item.id === activeSearchId}
                onClick={() => handleSearchHistoryClick(item)}
                onDelete={() => deleteSearchHistoryItem(item.id)}
                searchCount={item.searchCount}
              />
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No recent searches</p>
              <p className="text-sm mt-2">Your search history will appear here</p>
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200 bg-white">
          <button 
            className="w-full px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors flex items-center justify-center gap-2"
            onClick={clearSearchHistory}
            disabled={searchHistory.length === 0}
          >
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
                <SearchInput 
                  onSearch={handleSearch} 
                  isLoading={isSearching} 
                  initialQuery={currentQuery}
                />
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
