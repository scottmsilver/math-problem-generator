import React, { useState } from 'react';
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
  DialogActions,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import axios from '../utils/axios';

function GeneratedSets() {
  const { id: problemSetId } = useParams();
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState('claude');
  const [difficulty, setDifficulty] = useState('same');
  const [numProblems, setNumProblems] = useState(5);
  const queryClient = useQueryClient();

  const { data: generatedSets, isLoading } = useQuery({
    queryKey: ['generatedSets', problemSetId],
    queryFn: () =>
      axios.get(`/api/problem-sets/${problemSetId}/generated`).then((res) => res.data),
  });

  const generateSet = useMutation({
    mutationFn: async () => {
      try {
        const data = {
          provider,
          difficulty,
          num_problems: numProblems,
        };
        console.log('Sending data:', data);
        const response = await axios.post(`/api/problem-sets/${problemSetId}/generate`, data);
        return response.data;
      } catch (error) {
        console.error('Generate error:', error.response?.data || error);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['generatedSets', problemSetId]);
      setOpen(false);
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

      <Grid container spacing={3}>
        {generatedSets?.map((set) => (
          <Grid item xs={12} sm={6} md={4} key={set.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">
                  Generated on {new Date(set.created_at).toLocaleDateString()}
                </Typography>
                <Typography>Provider: {set.provider}</Typography>
                <Typography>Difficulty: {set.difficulty}</Typography>
                <Typography>Problems: {set.num_problems}</Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  onClick={() => handleDownload(set.id, 'problems')}
                >
                  Download Problems
                </Button>
                <Button
                  size="small"
                  onClick={() => handleDownload(set.id, 'solutions')}
                >
                  Download Solutions
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate New Problem Set</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Provider</InputLabel>
              <Select
                value={provider}
                label="Provider"
                onChange={(e) => setProvider(e.target.value)}
              >
                <MenuItem value="claude">Claude</MenuItem>
                <MenuItem value="gemini">Gemini</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Difficulty</InputLabel>
              <Select
                value={difficulty}
                label="Difficulty"
                onChange={(e) => setDifficulty(e.target.value)}
              >
                <MenuItem value="same">Same</MenuItem>
                <MenuItem value="challenge">Challenge</MenuItem>
                <MenuItem value="harder">Harder</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              type="number"
              label="Number of Problems"
              value={numProblems}
              onChange={(e) => setNumProblems(parseInt(e.target.value, 10))}
              inputProps={{ min: 1, max: 20 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
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
