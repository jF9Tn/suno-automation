// app/components/SidebarFilters.tsx
import BookFilter from "./BookFilter"; // Changed from GenreFilter
import { FilterIcon } from "./ui/icon";

interface FilterData {
  // testaments: ("Old Testament" | "New Testament")[]; // Removed
  bookNames: string[]; // Changed from genres
}

export interface ActiveFilters {
  // Exporting for use in other components if needed
  bookName: string | null; // Changed from genre
}

interface SidebarFiltersProps {
  filters: FilterData;
  activeFilters: ActiveFilters;
  onFilterChange: (newFilter: Partial<ActiveFilters>) => void;
}

export default function SidebarFilters({
  filters,
  activeFilters,
  onFilterChange,
}: SidebarFiltersProps) {
  return (
    <aside className="w-full md:w-1/4 space-y-6 p-4 bg-white rounded-lg shadow-sm border border-slate-200 self-start md:sticky md:top-8 md:max-h-[calc(100vh-4rem)] md:overflow-y-auto">
      <h2 className="text-xl font-semibold text-slate-700 border-b pb-2 mb-4 flex items-center sticky top-0 bg-white z-10">
        <FilterIcon className="w-5 h-5 mr-2 text-sky-600" />
        Filter Books
      </h2>
      {/* <TestamentFilter // Removed TestamentFilter
        testaments={filters.testaments}
        selectedTestament={activeFilters.testament}
        onSelectTestament={(testament: "Old Testament" | "New Testament") =>
          onFilterChange({
            testament: activeFilters.testament === testament ? null : testament,
          })
        }
      /> */}
      <BookFilter
        bookNames={filters.bookNames}
        selectedBookName={activeFilters.bookName}
        onSelectBookName={(bookName: string) =>
          onFilterChange({
            bookName: activeFilters.bookName === bookName ? null : bookName,
          })
        }
      />{" "}
      <button
        onClick={() =>
          onFilterChange({
            bookName: null,
          })
        }
        className="w-full mt-4 px-4 py-2 border border-slate-300 text-slate-700 rounded-md hover:bg-slate-100 text-sm"
      >
        Clear All Filters
      </button>
    </aside>
  );
}
