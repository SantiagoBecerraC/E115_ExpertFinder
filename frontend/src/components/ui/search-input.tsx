import { Input } from "./input"
import { Button } from "./button"
import { useState, useEffect } from "react"

interface SearchInputProps {
  onSearch: (query: string) => Promise<void>
  isLoading: boolean
  initialQuery?: string
}

export function SearchInput({ onSearch, isLoading, initialQuery = "" }: SearchInputProps) {
  const [query, setQuery] = useState(initialQuery)

  // Update query when initialQuery changes
  useEffect(() => {
    if (initialQuery) {
      setQuery(initialQuery)
    }
  }, [initialQuery])

  const handleSearch = async () => {
    if (!query.trim()) return
    await onSearch(query)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  return (
    <div className="flex w-full max-w-3xl gap-4 items-center">
      <div className="relative flex-1">
        <div className="absolute left-3 top-1/2 -translate-y-1/2">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="#2B95D6"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M17 8C17 10.7614 14.7614 13 12 13C9.23858 13 7 10.7614 7 8C7 5.23858 9.23858 3 12 3C14.7614 3 17 5.23858 17 8Z"
              fill="#2B95D6"
            />
            <path
              d="M12 14C8.13401 14 5 10.866 5 7C5 3.13401 8.13401 0 12 0C15.866 0 19 3.13401 19 7C19 8.93563 18.2275 10.6872 16.9793 11.9824L23.7071 18.7071C24.0976 19.0976 24.0976 19.7308 23.7071 20.1213C23.3166 20.5118 22.6834 20.5118 22.2929 20.1213L15.5651 13.3966C14.2829 14.4219 12.7051 15 11 15C10.3285 15 9.67818 14.8951 9.06522 14.6988C8.00492 14.3587 7.36/group-users.svg"
              fill="#2B95D6"
            />
          </svg>
        </div>
        <Input 
          className="pl-12 py-6 text-lg rounded-full border-2 border-gray-200" 
          placeholder="Need an AI/ML Expert? What skills or expertise you are looking for?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
        />
      </div>
      <Button 
        className="bg-[#2B95D6] text-white px-8 py-6 text-lg rounded-full hover:bg-[#2481bb]"
        onClick={handleSearch}
        disabled={isLoading || !query.trim()}
      >
        {isLoading ? "SEARCHING..." : "SUBMIT"}
      </Button>
    </div>
  )
}