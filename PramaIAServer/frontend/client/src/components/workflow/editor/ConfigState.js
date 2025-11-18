// ConfigState.js
// Hook custom per la gestione dello stato della configurazione
import { useState } from 'react';

export function useConfigState(initialConfig) {
  const [config, setConfig] = useState(initialConfig || {});
  const [errors, setErrors] = useState({});
  return { config, setConfig, errors, setErrors };
}
