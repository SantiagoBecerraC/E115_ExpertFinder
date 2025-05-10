# Expert Finder Frontend

A modern web application for finding and connecting with domain experts in Computer Science and Life Sciences.

## Project Structure
```
frontend/
├── src/
│   ├── app/                 # Next.js app directory
│   │   ├── page.tsx         # Main application page
│   │   └── experts/         # Experts routing
│   ├── components/          # React components
│   │   ├── ExpertList.tsx   # List of expert results
│   │   ├── ExpertCard.tsx   # Individual expert card
│   │   ├── ExpertTabs.tsx   # Tab navigation
│   │   ├── CredibilityBadge.tsx # Expert credibility indicator
│   │   └── ui/              # UI components
│   └── lib/                 # Utility functions and API
│       ├── api.ts           # API interface
│       └── utils.ts         # Helper functions
```

## Getting Started Locally

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Core Components

### 1. Main Page (`page.tsx`)
The main application page that handles:
- Search functionality
- Chat history display
- Feature showcase
- Expert results display

Key features:
- Real-time search with API integration
- Mock data for LinkedIn experts
- Responsive layout with sidebar
- Feature cards highlighting key capabilities

### 2. Expert Components

#### CredibilityBadge (`CredibilityBadge.tsx`)
A component that visually represents the credibility of an expert based on metrics such as citations, publications, and profile completeness. 

#### ExpertTabs (`ExpertTabs.tsx`)
- Handles tab navigation between LinkedIn and Google Scholar experts
- Displays filtered results based on source
- Manages tab state and switching
- Shows expert count for each source

#### ExpertList (`ExpertList.tsx`)
- Displays the list of expert results
- Handles filtering and sorting
- Shows expert details including:
  - Name and title
  - Company and location
  - Skills and interests
  - Citations and publications
- Implements responsive card layout
- Uses badges for source and skills/interests

#### ExpertCard (`ExpertCard.tsx`)
- Displays an expert's information in a card layout
- Shows expert details including:
  - Name and title
  - Company and location
  - Skills and interests
  - Citations and publications
- Implements responsive card layout
- Uses badges for source and skills/interests


### 3. API Integration (`api.ts`)
- Defines TypeScript interfaces for API data
- Handles API communication with error handling
- Provides type safety for expert data
- Implements fallback for failed requests

## Data Flow

1. User enters search query in `SearchInput`
2. `handleSearch` function in `page.tsx` makes API call to backend
3. Results are combined with mock LinkedIn data
4. `ExpertTabs` component receives results and filters by source
5. `ExpertList` displays filtered results using `ExpertCard`

## UI Components
Located in `components/ui/`:
- Search input with loading state
- Chat history items
- Tab navigation
- Cards and badges for expert information

## Styling
- Uses Tailwind CSS for styling
- Responsive design with mobile-first approach
- Consistent color scheme and typography
- Modern UI with hover effects and transitions
- Custom color schemes for LinkedIn (blue) and Scholar (purple)

## Dependencies
- Next.js 15.3.0
- React 19.0.0
- TypeScript 5.8
- Tailwind CSS 3.4
- Radix UI Components (Tabs, Select, Tooltip, Slot)
- Lucide React Icons
- Class Variance Authority
- Tailwind Merge

## Development
- Built with Next.js 15+ and App Router
- TypeScript for type safety
- Tailwind CSS for styling
- ESLint 9 for code quality

## API Integration
The frontend communicates with the backend API at `http://localhost:8000`:
- POST `/search` - Search for experts
- Request body: `{ query: string, max_results?: number }`
- Response: `{ experts: Expert[] }`






