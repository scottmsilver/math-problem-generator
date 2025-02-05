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
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import axios from '../utils/axios';

function GeneratedSets() {
  const { id: problemSetId } = useParams();
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('claude');
  const [difficulty, setDifficulty] = useState('same');
  const [numProblems, setNumProblems] = useState(5);
  const [progress, setProgress] = useState('');
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

  const generateSet = useMutation({
    mutationFn: async () => {
      try {
        setProgress('Starting generation...');
        const data = {
          provider,
          difficulty,
          num_problems: numProblems,
        };
        console.log('Sending generation request:', data);
        const response = await axios.post(`/api/problem-sets/${problemSetId}/generate`, data);
        console.log('Generation response:', response.data);
        return response.data;
      } catch (error) {
        console.error('Generate error:', error.response?.data || error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['generatedSets', problemSetId]);
      setOpen(false);
      setProgress('');
    },
    onError: (error) => {
      console.error('Generation failed:', error);
      setProgress('');
    },
  });

  const handleDownload = async (setId, type) => {
    try {
      const response = await axios.get(
        `/api/generated-sets/${setId}/download?type=${type}`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${type}_${setId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleGenerate = () => {
    generateSet.mutate();
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
                  href={`/api/generated-sets/${set.id}/download?type=problems`}
                  color="primary"
                  sx={{ mr: 1 }}
                >
                  Problems
                </Button>
                <Button 
                  href={`/api/generated-sets/${set.id}/download?type=solutions`}
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
      <Dialog open={open} onClose={() => !generateSet.isLoading && setOpen(false)}>
        <DialogTitle>Generate New Problem Set</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Choose your settings for the new problem set:
          </DialogContentText>
          <FormControl fullWidth margin="normal">
            <InputLabel>Provider</InputLabel>
            <Select value={provider} onChange={(e) => setProvider(e.target.value)}>
              <MenuItem value="claude">Claude</MenuItem>
              <MenuItem value="gemini">Gemini</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal">
            <InputLabel>Difficulty</InputLabel>
            <Select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
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
          {(generateSet.isLoading || progress) && (
            <Box sx={{ mt: 2 }}>
              <LinearProgress />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {progress || 'Preparing...'}
              </Typography>
            </Box>
          )}
          {generateSet.isError && (
            <Typography color="error" sx={{ mt: 2 }}>
              Error: {generateSet.error?.response?.data?.error || 'Failed to generate problems'}
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={generateSet.isLoading}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleGenerate}
            disabled={generateSet.isLoading}
          >
            {generateSet.isLoading ? 'Generating...' : 'Generate'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default GeneratedSets;
