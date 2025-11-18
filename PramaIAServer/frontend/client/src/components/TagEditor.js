import React, { useState } from 'react';

const TagEditor = ({ 
  tags = [], 
  onTagsChange, 
  category = '', 
  onCategoryChange, 
  color = '#3B82F6', 
  onColorChange,
  availableCategories = [],
  availableTags = [],
  className = '' 
}) => {
  const [newTag, setNewTag] = useState('');
  const [showColorPicker, setShowColorPicker] = useState(false);

  // Predefined colors for categories
  const predefinedColors = [
    '#3B82F6', // Blue
    '#EF4444', // Red
    '#10B981', // Green
    '#F59E0B', // Yellow
    '#8B5CF6', // Purple
    '#EC4899', // Pink
    '#06B6D4', // Cyan
    '#84CC16', // Lime
    '#F97316', // Orange
    '#6B7280'  // Gray
  ];

  // Predefined categories
  const predefinedCategories = [
    'General',
    'Business Process',
    'Data Analysis',
    'Content Generation',
    'Customer Service',
    'Marketing',
    'Development',
    'Research',
    'Automation',
    'Integration',
    'Legal',
    'Medical',
    'Financial',
    'Education',
    'E-commerce'
  ];

  const handleAddTag = (tagToAdd = null) => {
    const tag = tagToAdd || newTag.trim();
    if (tag && !tags.includes(tag)) {
      onTagsChange([...tags, tag]);
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    onTagsChange(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Category Section */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          📂 Categoria
        </label>
        <div className="flex gap-2">
          <select
            value={category}
            onChange={(e) => onCategoryChange(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Seleziona categoria...</option>
            {predefinedCategories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
            {availableCategories.filter(cat => !predefinedCategories.includes(cat)).map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          {/* Color Picker */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowColorPicker(!showColorPicker)}
              className="w-10 h-10 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              style={{ backgroundColor: color }}
              title="Scegli colore categoria"
            />
            
            {showColorPicker && (
              <div className="absolute top-12 right-0 bg-white border border-gray-300 rounded-lg shadow-lg p-3 z-10">
                <div className="grid grid-cols-5 gap-2">
                  {predefinedColors.map(colorOption => (
                    <button
                      key={colorOption}
                      type="button"
                      onClick={() => {
                        onColorChange(colorOption);
                        setShowColorPicker(false);
                      }}
                      className="w-8 h-8 rounded-md border border-gray-300 hover:scale-110 transition-transform"
                      style={{ backgroundColor: colorOption }}
                    />
                  ))}
                </div>
                <div className="mt-2">
                  <input
                    type="color"
                    value={color}
                    onChange={(e) => onColorChange(e.target.value)}
                    className="w-full h-8 rounded border border-gray-300"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Category Preview */}
        {category && (
          <div className="mt-2">
            <span 
              className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium text-white"
              style={{ backgroundColor: color }}
            >
              📂 {category}
            </span>
          </div>
        )}
      </div>

      {/* Tags Section */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          🏷️ Tag ({tags.length})
        </label>
        
        {/* Tag Input */}
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Aggiungi un tag..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          <button
            type="button"
            onClick={() => handleAddTag()}
            disabled={!newTag.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Aggiungi
          </button>
        </div>

        {/* Suggested Tags */}
        {availableTags.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-gray-500 mb-2">Tag suggeriti:</div>
            <div className="flex flex-wrap gap-1">
              {availableTags
                .filter(tag => !tags.includes(tag) && tag.toLowerCase().includes(newTag.toLowerCase()))
                .slice(0, 10)
                .map(tag => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => handleAddTag(tag)}
                    className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
                  >
                    + {tag}
                  </button>
                ))
              }
            </div>
          </div>
        )}

        {/* Current Tags */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <span 
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-100 text-indigo-800 border border-indigo-200"
              >
                🏷️ {tag}
                <button
                  type="button"
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-2 text-indigo-600 hover:text-indigo-800 focus:outline-none"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}

        {tags.length === 0 && (
          <div className="text-sm text-gray-500 italic">
            Nessun tag aggiunto. I tag aiutano a organizzare e trovare i workflow.
          </div>
        )}
      </div>

      {/* Quick Add Popular Tags */}
      <div>
        <div className="text-xs text-gray-500 mb-2">Tag popolari:</div>
        <div className="flex flex-wrap gap-1">
          {[
            'Analisi Documenti', 'Chat', 'OCR', 'Traduzione', 'Email', 
            'Report', 'Automazione', 'AI', 'NLP', 'Ricerca'
          ].filter(tag => !tags.includes(tag)).map(tag => (
            <button
              key={tag}
              type="button"
              onClick={() => handleAddTag(tag)}
              className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition-colors"
            >
              + {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Click outside to close color picker */}
      {showColorPicker && (
        <div 
          className="fixed inset-0 z-5"
          onClick={() => setShowColorPicker(false)}
        />
      )}
    </div>
  );
};

export default TagEditor;
