import React, { createContext, useContext } from 'react';

const TabsContext = createContext();

const Tabs = ({ children, defaultValue, value, onValueChange, className = '', ...props }) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue || value);

  const handleTabChange = (newValue) => {
    if (onValueChange) {
      onValueChange(newValue);
    } else {
      setActiveTab(newValue);
    }
  };

  const currentValue = value !== undefined ? value : activeTab;

  return (
    <TabsContext.Provider value={{ value: currentValue, onValueChange: handleTabChange }}>
      <div className={`w-full ${className}`} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

const TabsList = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={`inline-flex h-9 items-center justify-center rounded-lg bg-gray-100 p-1 text-gray-500 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

const TabsTrigger = ({ children, value, className = '', ...props }) => {
  const context = useContext(TabsContext);
  const isActive = context.value === value;

  return (
    <button
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${
        isActive 
          ? 'bg-white text-gray-900 shadow' 
          : 'text-gray-600 hover:text-gray-900'
      } ${className}`}
      onClick={() => context.onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  );
};

const TabsContent = ({ children, value, className = '', ...props }) => {
  const context = useContext(TabsContext);
  
  if (context.value !== value) {
    return null;
  }

  return (
    <div 
      className={`mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export { Tabs, TabsList, TabsTrigger, TabsContent };
