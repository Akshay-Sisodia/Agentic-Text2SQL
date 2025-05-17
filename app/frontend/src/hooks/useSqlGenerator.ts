import { useState } from 'react';
import { useMutation } from 'react-query';
import { apiService } from '../services/apiService';
import type { Text2SQLResponse, Text2SQLRequest } from '../types/api';

export const useSqlGenerator = () => {
  const [result, setResult] = useState<Text2SQLResponse | null>(null);
  
  const { mutateAsync, isLoading, error } = useMutation(
    (request: Text2SQLRequest) => apiService.processSqlQuery(request),
    {
      onSuccess: (data) => {
        setResult(data);
        // Store conversation ID for future reference
        if (data.conversation_id) {
          localStorage.setItem('conversation_id', data.conversation_id);
        }
      },
    }
  );
  
  const generateSql = async (request: Text2SQLRequest) => {
    try {
      await mutateAsync(request);
    } catch (error) {
      console.error('Failed to generate SQL:', error);
    }
  };
  
  return {
    generateSql,
    result,
    isLoading,
    error: error ? (error as Error).message : null,
  };
}; 