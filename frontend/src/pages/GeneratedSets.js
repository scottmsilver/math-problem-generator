import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Stack,
  IconButton,
} from '@mui/material';
import {
  Add as AddIcon,
  Download as DownloadIcon,
  Close as CloseIcon,
  ErrorOutline as ErrorOutlineIcon,
  Replay as ReplayIcon
} from '@mui/icons-material';
import axios from '../utils/axios';
import { downloadService } from '../services/downloadService';

function GeneratedSets() {
  const { id: problemSetId } = useParams();
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('claude');
  const [difficulty, setDifficulty] = useState('same');
  const [numProblems, setNumProblems] = useState(5);
  const [progress, setProgress] = useState('');
  const [generationStarted, setGenerationStarted] = useState(false);
  const [generatedSettings, setGeneratedSettings] = useState(null);
  const [isNewSet, setIsNewSet] = useState(true);
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    console.log('Creating EventSource connection...');
    const eventSource = new EventSource(`http://localhost:8081/api/events?token=${token}`, {
      withCredentials: true
    });
    
    eventSource.onopen = () => {
      console.log('SSE connection opened');
    };
    
    eventSource.onmessage = (event) => {
      console.log('SSE message received:', event.data);
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'progress') {
          console.log('Progress update:', data.message);
          setProgress(data.message);
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      if (eventSource.readyState === EventSource.CLOSED) {
        console.log('SSE connection closed');
      }
      eventSource.close();
    };

    return () => {
      console.log('Closing SSE connection');
      eventSource.close();
    };
  }, []);

  const { data: generatedSets, isLoading } = useQuery({
    queryKey: ['generatedSets', problemSetId],
    queryFn: async () =>
      axios.get(`/api/problem-sets/${problemSetId}/generated`).then((res) => res.data),
  });

  const handleClose = () => {
    setOpen(false);
    setIsNewSet(true);
    setGenerationStarted(false);
    setProgress('');
    generateSet.reset();
    setGeneratedSettings(null);
  };

  const handleGenerate = () => {
    setGeneratedSettings({
      provider,
      difficulty,
      numProblems
    });
    setIsNewSet(false);
    setGenerationStarted(true);
    generateSet.mutate();
  };

  const generateSet = useMutation({
    mutationFn: async () => {
      try {
        const data = {
          provider,
          difficulty,
          num_problems: numProblems,
        };
        const response = await axios.post(`/api/problem-sets/${problemSetId}/generate`, data);
        return response.data;
      } catch (error) {
        console.error('Generate error:', error.response?.data || error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['generatedSets', problemSetId]);
    },
    onSettled: () => {
      setGenerationStarted(false);
    },
    onError: (error) => {
      console.error('Generation failed:', error);
      setProgress('');
    },
  });

  const handleDownload = async (type, setId) => {
    try {
      await downloadService.downloadFile(
        `/api/generated-sets/${setId}/download?type=${type}`,
        `${type}.pdf`
      );
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h4">Generated Sets</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          Generate New Set
        </Button>
      </Box>

      {/* Generated Sets List */}
      <Box sx={{ mt: 3 }}>
        <List>
          {generatedSets?.map((set) => (
            <ListItem 
              key={set.id}
              divider
              sx={{ 
                backgroundColor: 'background.paper',
                borderRadius: 1,
                mb: 1,
                '&:hover': {
                  backgroundColor: 'action.hover',
                }
              }}
            >
              <ListItemText
                primary={
                  <Typography variant="subtitle1">
                    Generated {new Date(set.created_at).toLocaleString()}
                  </Typography>
                }
                secondary={
                  <Typography variant="body2" color="text.secondary">
                    {set.num_problems} problems • {set.difficulty} difficulty • {set.provider.toLowerCase()} provider
                  </Typography>
                }
              />
              <ListItemSecondaryAction>
                <Button 
                  onClick={() => handleDownload('problems', set.id)}
                  color="primary"
                  sx={{ mr: 1 }}
                >
                  Problems
                </Button>
                <Button 
                  onClick={() => handleDownload('solutions', set.id)}
                  color="secondary"
                >
                  Solutions
                </Button>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Box>

      {/* Generation Dialog */}
      <Dialog open={open} onClose={handleClose}>
        <Box sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h6" component="div">
              {isNewSet ? "Create New Problem Set" : generateSet.isSuccess ? "Generation Report" : "Generating Problem Set"}
            </Typography>
            <IconButton onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>

          {isNewSet ? (
            <Box>
              <FormControl fullWidth margin="normal">
                <InputLabel>Provider</InputLabel>
                <Select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                >
                  <MenuItem value="claude">Claude</MenuItem>
                  <MenuItem value="gemini">Gemini</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth margin="normal">
                <InputLabel>Difficulty</InputLabel>
                <Select
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                >
                  <MenuItem value="same">Same</MenuItem>
                  <MenuItem value="challenge">Challenge</MenuItem>
                  <MenuItem value="harder">Harder</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth margin="normal">
                <TextField
                  label="Number of Problems"
                  type="number"
                  value={numProblems}
                  onChange={(e) => setNumProblems(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 20 }}
                />
              </FormControl>

              <Button 
                variant="contained" 
                onClick={handleGenerate}
                fullWidth
                sx={{ mt: 2 }}
              >
                Generate
              </Button>
            </Box>
          ) : (
            <Box>
              {/* Settings Summary */}
              <Box sx={{ 
                bgcolor: 'background.paper',
                borderRadius: 1,
                p: 2,
                mb: 3,
                border: '1px solid',
                borderColor: 'divider'
              }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Generation Settings
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Typography variant="body2">Provider:</Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {generatedSettings?.provider}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2">Difficulty:</Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {generatedSettings?.difficulty}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2">Problem Count:</Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {generatedSettings?.numProblems}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

              {/* Progress and Results */}
              {generationStarted && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress sx={{ mb: 2 }}/>
                  <Typography variant="body2" color="text.secondary">
                    {progress || 'Initializing generation process...'}
                  </Typography>
                </Box>
              )}

              {generateSet.isSuccess && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" color="success.main" gutterBottom>
                    Generation Completed Successfully
                  </Typography>
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      onClick={() => handleDownload('problems', generateSet.data.id)}
                      startIcon={<DownloadIcon />}
                    >
                      Problems PDF
                    </Button>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={() => handleDownload('solutions', generateSet.data.id)}
                      startIcon={<DownloadIcon />}
                    >
                      Solutions PDF
                    </Button>
                  </Stack>
                </Box>
              )}

              {generateSet.isError && (
                <Box sx={{ mt: 3 }}>
                  <Box sx={{ 
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 2,
                    color: 'error.main'
                  }}>
                    <ErrorOutlineIcon />
                    <Typography variant="subtitle2">
                      Generation Failed
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {generateSet.error?.response?.data?.error || 'An unexpected error occurred during generation'}
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => generateSet.mutate()}
                    startIcon={<ReplayIcon />}
                  >
                    Retry Generation
                  </Button>
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Dialog>
    </>
  );
}

export default GeneratedSets;
