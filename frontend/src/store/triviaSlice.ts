import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';

interface Question {
  question: string;
  options: string[];
  correct_answer: string;
}

interface TriviaState {
  questions: Question[];
  currentQuestionIndex: number;
  score: number;
  loading: boolean;
  error: string | null;
}

const initialState: TriviaState = {
  questions: [],
  currentQuestionIndex: 0,
  score: 0,
  loading: false,
  error: null,
};

interface GenerateQuestionsParams {
  documentType: string;
  documentContent: string;
}

export const fetchQuestions = createAsyncThunk(
  'trivia/fetchQuestions',
  async ({ documentType, documentContent }: GenerateQuestionsParams) => {
    const response = await axios.post('http://localhost:5000/api/generate', {
      document_type: documentType,
      document_content: documentContent,
    });
    return response.data.questions;
  }
);

const triviaSlice = createSlice({
  name: 'trivia',
  initialState,
  reducers: {
    submitAnswer: (state, action: PayloadAction<string>) => {
      const currentQuestion = state.questions[state.currentQuestionIndex];
      if (action.payload === currentQuestion.correct_answer) {
        state.score += 1;
      }
      if (state.currentQuestionIndex < state.questions.length - 1) {
        state.currentQuestionIndex += 1;
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchQuestions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchQuestions.fulfilled, (state, action) => {
        state.loading = false;
        state.questions = action.payload;
        state.currentQuestionIndex = 0;
        state.score = 0;
      })
      .addCase(fetchQuestions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取问题失败';
      });
  },
});

export const { submitAnswer } = triviaSlice.actions;
export default triviaSlice.reducer; 