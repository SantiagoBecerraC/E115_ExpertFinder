interface ChatHistoryItemProps {
  title: string
  timestamp: string
  isActive?: boolean
  onClick?: () => void
  preview?: string
  expertCount?: number
}

export function ChatHistoryItem({
  title,
  timestamp,
  isActive = false,
  onClick,
  preview = "",
  expertCount = 0
}: ChatHistoryItemProps) {
  return (
    <div
      onClick={onClick}
      className={`p-4 rounded-lg cursor-pointer transition-all ${
        isActive
          ? 'bg-blue-50 border-2 border-blue-200'
          : 'bg-white border border-gray-100 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
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
          </div>
        </div>
        <div className={`w-2 h-2 rounded-full mt-2 ${isActive ? 'bg-blue-500' : 'bg-gray-200'}`} />
      </div>
    </div>
  )
} 