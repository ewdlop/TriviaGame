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
  baseQuery: fetchBaseQuery({ baseUrl: 'http://localhost:8000' }),
  endpoints: (builder) => ({
    generateQuestion: builder.mutation<Question, GenerateQuestionRequest>({
      query: (body) => ({
        url: '/api/generate-question',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const { useGenerateQuestionMutation } = triviaApi; 