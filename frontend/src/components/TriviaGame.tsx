import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Paper,
} from '@mui/material';
import { RootState } from '../store/store';
import { incrementScore } from '../store/triviaSlice';
import { useGenerateQuestionMutation, useUploadDocumentMutation } from '../store/triviaApi';

const TriviaGame: React.FC = () => {
  const dispatch = useDispatch();
  const { score } = useSelector((state: RootState) => state.trivia);
  const [generateQuestion, { data: currentQuestion, isLoading: isGenerating, error: generateError }] = useGenerateQuestionMutation();
  const [uploadDocument, { isLoading: isUploading, error: uploadError }] = useUploadDocumentMutation();
  
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const result = await uploadDocument(formData).unwrap();
      setUploadMessage(result.message);
    } catch (err) {
      console.error('Failed to upload document:', err);
    }
  };

  const handleGenerateQuestion = async () => {
    try {
      await generateQuestion({
        question: topic,
        difficulty,
      }).unwrap();
      setSelectedAnswer(null);
      setShowExplanation(false);
    } catch (err) {
      console.error('Failed to generate question:', err);
    }
  };

  const handleAnswerSelect = (answer: string) => {
    setSelectedAnswer(answer);
    setShowExplanation(true);
    if (answer === currentQuestion?.correct_answer) {
      dispatch(incrementScore());
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      <Typography variant="h4" gutterBottom>
        问答游戏
      </Typography>
      <Typography variant="h6" gutterBottom>
        得分: {score}
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          上传文档
        </Typography>
        <input
          accept=".pdf,.md,.txt"
          style={{ display: 'none' }}
          id="document-upload"
          type="file"
          onChange={handleFileUpload}
        />
        <label htmlFor="document-upload">
          <Button
            variant="contained"
            component="span"
            disabled={isUploading}
          >
            {isUploading ? <CircularProgress size={24} /> : '选择文档'}
          </Button>
        </label>
        {uploadMessage && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {uploadMessage}
          </Alert>
        )}
        {uploadError && (
          <Alert severity="error" sx={{ mt: 2 }}>
            文档上传失败
          </Alert>
        )}
      </Paper>

      <Box sx={{ mb: 3 }}>
        <TextField
          fullWidth
          label="输入主题"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          sx={{ mb: 2 }}
        />
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>难度</InputLabel>
          <Select
            value={difficulty}
            label="难度"
            onChange={(e) => setDifficulty(e.target.value)}
          >
            <MenuItem value="easy">简单</MenuItem>
            <MenuItem value="medium">中等</MenuItem>
            <MenuItem value="hard">困难</MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="contained"
          onClick={handleGenerateQuestion}
          disabled={isGenerating || !topic}
        >
          {isGenerating ? <CircularProgress size={24} /> : '生成问题'}
        </Button>
      </Box>

      {generateError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          生成问题失败
        </Alert>
      )}

      {currentQuestion && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              {currentQuestion.question}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {currentQuestion.options.map((option, index) => (
                <Button
                  key={index}
                  variant={
                    selectedAnswer === option
                      ? option === currentQuestion.correct_answer
                        ? 'contained'
                        : 'outlined'
                      : 'outlined'
                  }
                  color={
                    selectedAnswer === option
                      ? option === currentQuestion.correct_answer
                        ? 'success'
                        : 'error'
                      : 'primary'
                  }
                  onClick={() => handleAnswerSelect(option)}
                  disabled={showExplanation}
                >
                  {option}
                </Button>
              ))}
            </Box>
            {showExplanation && (
              <Typography sx={{ mt: 2 }} color="text.secondary">
                解释: {currentQuestion.explanation}
              </Typography>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default TriviaGame; 