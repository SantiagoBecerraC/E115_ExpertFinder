interface ChatHistoryItemProps {
  title: string
  timestamp: string
  isActive?: boolean
  onClick?: () => void
  onDelete?: () => void
  preview?: string
  expertCount?: number
  searchCount?: number
}

export function ChatHistoryItem({
  title,
  timestamp,
  isActive = false,
  onClick,
  onDelete,
  preview = "",
  expertCount = 0,
  searchCount = 1
}: ChatHistoryItemProps) {
  return (
    <div
      className={`p-4 rounded-lg cursor-pointer transition-all relative group ${
        isActive
          ? 'bg-blue-50 border-2 border-blue-200'
          : 'bg-white border border-gray-100 hover:bg-gray-50'
      }`}
    >
      {/* Delete button - visible on hover */}
      {onDelete && (
        <button 
          onClick={(e) => {
            e.stopPropagation(); // Prevent triggering the parent onClick
            onDelete();
          }}
          className="absolute top-2 right-2 p-1 rounded-full bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-gray-200"
          aria-label="Delete search history item"
        >
          <svg className="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
      
      <div 
        onClick={onClick}
        className="flex items-start justify-between gap-2"
      >
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-gray-900 truncate mb-1">
            {title}
          </h3>
          <p className="text-sm text-gray-500 line-clamp-2 mb-2">
            {preview || "Search for experts in this field..."}
          </p>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-400">{timestamp}</span>
            {expertCount > 0 && (
              <>
                <span className="text-gray-300">•</span>
                <span className="text-blue-600 font-medium">
                  {expertCount} expert{expertCount !== 1 ? 's' : ''} found
                </span>
              </>
            )}
            {searchCount > 1 && (
              <>
                <span className="text-gray-300">•</span>
                <span className="text-purple-600 font-medium">
                  Searched {searchCount} times
                </span>
              </>
            )}
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full mt-2 ${isActive ? 'bg-blue-500' : 'bg-gray-200'}`} />
      </div>
    </div>
  )
}