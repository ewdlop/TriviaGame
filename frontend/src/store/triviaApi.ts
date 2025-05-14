import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

interface Question {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

interface GenerateQuestionRequest {
  question: string;
  difficulty: string;
}

export const triviaApi = createApi({
  reducerPath: 'triviaApi',
  baseQuery: fetchBaseQuery({ 
    baseUrl: 'http://localhost:8000',
    // 设置较长的超时时间，因为Ollama生成可能需要更长时间
    timeout: 30000,
  }),
  endpoints: (builder) => ({
    generateQuestion: builder.mutation<Question, GenerateQuestionRequest>({
      query: (body) => ({
        url: '/api/generate-question',
        method: 'POST',
        body,
      }),
    }),
    uploadDocument: builder.mutation<{ message: string }, FormData>({
      query: (formData) => ({
        url: '/api/upload-document',
        method: 'POST',
        body: formData,
      }),
    }),
  }),
});

export const { useGenerateQuestionMutation, useUploadDocumentMutation } = triviaApi; 