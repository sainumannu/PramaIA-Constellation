/**
 * PDK Tag Management Components
 * Simplified React components for PramaIA frontend integration
 */

import React, { useState, useMemo, useCallback } from 'react';

// Simple Tag Badge Component
export const PDKTagBadge = ({ 
  tag, 
  variant = 'solid', 
  size = 'sm', 
  colorScheme, 
  isRemovable = false, 
  onClick, 
  onRemove 
}) => {
  const getColorClass = (tag, scheme) => {
    if (scheme) return `bg-${scheme}-100 text-${scheme}-800 border-${scheme}-200`;
    
    // Auto-generate color based on tag hash
    const colors = ['blue', 'green', 'purple', 'red', 'orange', 'yellow', 'pink', 'indigo'];
    const hash = tag.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
    const color = colors[hash % colors.length];
    
    return variant === 'outline' 
      ? `bg-white text-${color}-600 border-${color}-300 hover:bg-${color}-50`
      : `bg-${color}-100 text-${color}-800 border-${color}-200`;
  };

  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm', 
    lg: 'px-4 py-2 text-base'
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full border font-medium
        ${getColorClass(tag, colorScheme)}
        ${sizeClasses[size]}
        ${onClick ? 'cursor-pointer hover:opacity-80' : ''}
        transition-opacity
      `}
      onClick={onClick ? () => onClick(tag) : undefined}
    >
      {tag}
      {isRemovable && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onRemove?.(tag);
          }}
          className="ml-1 hover:bg-red-200 rounded-full p-0.5 text-red-600"
        >
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </span>
  );
};

// Tag Filter Component
export const PDKTagFilter = ({ 
  availableTags = [], 
  selectedTags = [], 
  onTagsChange,
  mode = 'OR',
  onModeChange,
  placeholder = "Search tags..."
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  
  const filteredTags = useMemo(() => {
    if (!searchTerm) return availableTags;
    return availableTags.filter(tag => 
      tag.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [availableTags, searchTerm]);

  const handleTagToggle = useCallback((tag) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    onTagsChange?.(newTags);
  }, [selectedTags, onTagsChange]);

  return (
    <div className="relative">
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <input
            type="text"
            placeholder={placeholder}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onFocus={() => setIsOpen(true)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {onModeChange && (
            <select
              value={mode}
              onChange={(e) => onModeChange(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="OR">Any tag (OR)</option>
              <option value="AND">All tags (AND)</option>
            </select>
          )}
          {selectedTags.length > 0 && (
            <button
              onClick={() => onTagsChange?.([])}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-md"
            >
              Clear All
            </button>
          )}
        </div>

        {/* Selected Tags */}
        {selectedTags.length > 0 && (
          <div className="mb-3">
            <div className="text-sm font-medium text-gray-700 mb-2">
              Selected ({selectedTags.length}):
            </div>
            <div className="flex flex-wrap gap-2">
              {selectedTags.map(tag => (
                <PDKTagBadge
                  key={tag}
                  tag={tag}
                  isRemovable
                  onRemove={handleTagToggle}
                />
              ))}
            </div>
          </div>
        )}

        {/* Available Tags Dropdown */}
        {isOpen && filteredTags.length > 0 && (
          <div className="absolute z-50 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
            <div className="p-2">
              <div className="text-sm font-medium text-gray-700 mb-2">
                Available Tags ({filteredTags.length}):
              </div>
              <div className="space-y-1">
                {filteredTags.map(tag => (
                  <label key={tag} className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer">
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag)}
                      onChange={() => handleTagToggle(tag)}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <PDKTagBadge tag={tag} />
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

// Tag Cloud Component
export const PDKTagCloud = ({ 
  tagStats = [], 
  onTagClick, 
  maxTags = 50 
}) => {
  const displayTags = useMemo(() => {
    return tagStats.slice(0, maxTags);
  }, [tagStats, maxTags]);

  const getTagSize = useCallback((stat) => {
    const maxCount = Math.max(...tagStats.map(t => t.count));
    const minCount = Math.min(...tagStats.map(t => t.count));
    const ratio = (stat.count - minCount) / (maxCount - minCount);
    
    if (ratio > 0.8) return 'lg';
    if (ratio > 0.6) return 'md';
    return 'sm';
  }, [tagStats]);

  return (
    <div className="flex flex-wrap gap-2 justify-center">
      {displayTags.map((stat) => (
        <div key={stat.tag} className="relative group">
          <PDKTagBadge
            tag={stat.tag}
            size={getTagSize(stat)}
            onClick={onTagClick}
          />
          {/* Tooltip */}
          <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
            {stat.count} items ({stat.percentage}%)
          </div>
        </div>
      ))}
    </div>
  );
};

// Tag Statistics Component
export const PDKTagStats = ({ tagStats = [] }) => {
  const totalTags = tagStats.length;
  const totalItems = useMemo(() => {
    return tagStats.reduce((sum, stat) => sum + stat.count, 0);
  }, [tagStats]);
  const topTags = useMemo(() => tagStats.slice(0, 10), [tagStats]);

  return (
    <div className="space-y-4">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{totalTags}</div>
          <div className="text-sm text-blue-800">Total Tags</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{totalItems}</div>
          <div className="text-sm text-green-800">Total Items</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">
            {totalItems > 0 ? (totalTags / totalItems).toFixed(1) : 0}
          </div>
          <div className="text-sm text-purple-800">Avg Tags/Item</div>
        </div>
      </div>

      {/* Top Tags */}
      {topTags.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Top Tags</h3>
          <div className="space-y-2">
            {topTags.map((stat, index) => (
              <div key={stat.tag} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                  <PDKTagBadge tag={stat.tag} />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">
                    {stat.count} ({stat.percentage}%)
                  </span>
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${Math.min(100, stat.percentage)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Main Tag Management Panel
export const PDKTagManagementPanel = ({ 
  items = [], 
  onItemsFilter,
  showStats = true,
  showCloud = true 
}) => {
  const [selectedTags, setSelectedTags] = useState([]);
  const [filterMode, setFilterMode] = useState('OR');
  
  const availableTags = useMemo(() => {
    const tagSet = new Set();
    items.forEach(item => {
      (item.tags || []).forEach(tag => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }, [items]);

  const tagStats = useMemo(() => {
    const tagCounts = {};
    items.forEach(item => {
      (item.tags || []).forEach(tag => {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      });
    });

    const total = items.length;
    return Object.entries(tagCounts)
      .map(([tag, count]) => ({
        tag,
        count,
        percentage: ((count / total) * 100).toFixed(1)
      }))
      .sort((a, b) => b.count - a.count);
  }, [items]);

  const filteredItems = useMemo(() => {
    if (selectedTags.length === 0) return items;
    
    return items.filter(item => {
      const itemTags = (item.tags || []).map(t => t.toLowerCase());
      const searchTags = selectedTags.map(t => t.toLowerCase());
      
      if (filterMode === 'AND') {
        return searchTags.every(tag => itemTags.includes(tag));
      } else {
        return searchTags.some(tag => itemTags.includes(tag));
      }
    });
  }, [items, selectedTags, filterMode]);

  // Update parent when filtered items change
  React.useEffect(() => {
    onItemsFilter?.(filteredItems);
  }, [filteredItems, onItemsFilter]);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Tag Filter</h3>
        <PDKTagFilter
          availableTags={availableTags}
          selectedTags={selectedTags}
          onTagsChange={setSelectedTags}
          mode={filterMode}
          onModeChange={setFilterMode}
        />
      </div>

      {showCloud && tagStats.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Tag Cloud</h3>
          <PDKTagCloud
            tagStats={tagStats}
            onTagClick={(tag) => {
              if (!selectedTags.includes(tag)) {
                setSelectedTags([...selectedTags, tag]);
              }
            }}
          />
        </div>
      )}

      {showStats && (
        <div>
          <h3 className="text-lg font-semibold mb-4">Statistics</h3>
          <PDKTagStats tagStats={tagStats} />
        </div>
      )}
    </div>
  );
};

export default PDKTagManagementPanel;
