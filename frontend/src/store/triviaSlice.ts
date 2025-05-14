import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface Question {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

interface TriviaState {
  currentQuestion: Question | null;
  loading: boolean;
  error: string | null;
  score: number;
}

const initialState: TriviaState = {
  currentQuestion: null,
  loading: false,
  error: null,
  score: 0,
};

export const generateQuestion = createAsyncThunk(
  'trivia/generateQuestion',
  async ({ topic, difficulty }: { topic: string; difficulty: string }) => {
    const response = await axios.post('http://localhost:8000/api/generate-question', {
      question: topic,
      difficulty,
    });
    return response.data;
  }
);

const triviaSlice = createSlice({
  name: 'trivia',
  initialState,
  reducers: {
    incrementScore: (state) => {
      state.score += 1;
    },
    resetScore: (state) => {
      state.score = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(generateQuestion.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(generateQuestion.fulfilled, (state, action) => {
        state.loading = false;
        state.currentQuestion = action.payload;
      })
      .addCase(generateQuestion.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '生成问题失败';
      });
  },
});

export const { incrementScore, resetScore } = triviaSlice.actions;
export default triviaSlice.reducer; 