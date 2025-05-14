import { createSlice } from '@reduxjs/toolkit';

interface TriviaState {
  score: number;
}

const initialState: TriviaState = {
  score: 0,
};

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
});

export const { incrementScore, resetScore } = triviaSlice.actions;
export default triviaSlice.reducer; 