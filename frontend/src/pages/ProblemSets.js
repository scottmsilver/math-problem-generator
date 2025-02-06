import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  TextField,
  Typography,
  CircularProgress,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon, Upload as UploadIcon } from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from '../utils/axios';
import { formatDistanceToNow } from 'date-fns';
import { useSnackbar } from 'notistack';

function ProblemSets() {
  const { enqueueSnackbar } = useSnackbar();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [template, setTemplate] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [inputMethod, setInputMethod] = useState('pdf');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: '.pdf',
    onDrop: (files) => {
      if(files[0].type !== 'application/pdf') {
        enqueueSnackbar('Only PDF files supported', { variant: 'error' });
        return;
      }
      const file = files[0];
      setSelectedFile(file);
      if (!name) {
        setName(file.name.replace('.pdf', ''));
      }
    },
    disabled: inputMethod === 'latex' || isUploading,
  });

  const { data: problemSets, isLoading, error } = useQuery({
    queryKey: ['problemSets'],
    queryFn: async () => {
      try {
        const response = await axios.get('/api/problem-sets');
        return response.data;
      } catch (error) {
        console.error('Error fetching problem sets:', error.response || error);
        if (error.response?.status === 401) {
          window.location.href = '/login';
        }
        throw error;
      }
    },
  });

  if (error) {
    console.error('Problem sets query error:', error);
  }

  const createProblemSetWithFile = useMutation({
    mutationFn: (formData) => {
      setIsUploading(true);
      setUploadProgress(0);
      
      console.log('Sending request with headers:', {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
      });
      
      return axios.post('/api/problem-sets', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          console.log('Upload progress:', progress);
          setUploadProgress(progress);
        },
      });
    },
    onSuccess: (response) => {
      console.log('Upload success:', response.data);
      queryClient.invalidateQueries(['problemSets']);
      setOpen(false);
      setName('');
      setTemplate('');
      setUploadProgress(0);
      setSelectedFile(null);
      setIsUploading(false);
    },
    onError: (error) => {
      console.error('Upload error details:', {
        error,
        response: error.response,
        data: error.response?.data,
        status: error.response?.status,
      });
      setIsUploading(false);
      setUploadProgress(0);
      if (error.response?.status === 401) {
        window.location.href = '/login';
      } else {
        alert(error.response?.data?.error || 'Error uploading file. Please check the console for details.');
      }
    }
  });

  const createProblemSetWithLatex = useMutation({
    mutationFn: (data) => axios.post('/api/problem-sets', data),
    onSuccess: () => {
      queryClient.invalidateQueries(['problemSets']);
      setOpen(false);
      setName('');
      setTemplate('');
    },
  });

  const handleSubmit = () => {
    if (!name.trim()) {
      alert('Please enter a name for the problem set');
      return;
    }

    if (inputMethod === 'latex') {
      if (!template.trim()) {
        alert('Please enter a LaTeX template');
        return;
      }
      createProblemSetWithLatex.mutate({
        name: name.trim(),
        template: template.trim(),
      });
    } else if (selectedFile) {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('name', name.trim());
      
      console.log('Form data entries:');
      for (let [key, value] of formData.entries()) {
        console.log(key, value);
      }
      
      createProblemSetWithFile.mutate(formData);
    }
  };

  const handleNavigate = (id) => {
    navigate(`/problem-sets/${id}/generated`);
  };

  if (isLoading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between' }}>
        <Typography variant="h4">Problem Sets</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          Create New Set
        </Button>
      </Box>

      <Box sx={{ mt: 3 }}>
        <List>
          {problemSets?.map((set) => (
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
                primary={set.name}
                secondary={`Created ${formatDistanceToNow(new Date(set.created_at))} • ${set.generated_sets_count} generated sets`}
              />
              <ListItemSecondaryAction>
                <IconButton edge="end" onClick={() => handleNavigate(set.id)}>
                  <AddIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Problem Set</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              sx={{ mb: 2 }}
            />
            <Tabs
              value={inputMethod}
              onChange={(e, newValue) => {
                setInputMethod(newValue);
                setSelectedFile(null);
                setUploadProgress(0);
              }}
              sx={{ mb: 2 }}
            >
              <Tab label="Upload PDF" value="pdf" />
              <Tab label="Enter LaTeX" value="latex" />
            </Tabs>

            {inputMethod === 'pdf' ? (
              <Box
                {...getRootProps()}
                sx={{
                  border: '2px dashed',
                  borderColor: isUploading ? 'primary.main' : (isDragActive ? 'secondary.main' : 'primary.main'),
                  borderRadius: 1,
                  p: 3,
                  textAlign: 'center',
                  cursor: isUploading ? 'default' : 'pointer',
                  mb: 2,
                  position: 'relative',
                  bgcolor: isUploading ? 'action.hover' : 'transparent',
                }}
              >
                <input {...getInputProps()} />
                {isUploading ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <Box sx={{ position: 'relative', display: 'inline-flex', mb: 2 }}>
                      <CircularProgress variant="determinate" value={uploadProgress} size={60} />
                      <Box
                        sx={{
                          top: 0,
                          left: 0,
                          bottom: 0,
                          right: 0,
                          position: 'absolute',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Typography variant="caption" component="div" color="text.secondary">
                          {`${Math.round(uploadProgress)}%`}
                        </Typography>
                      </Box>
                    </Box>
                    <Typography>Uploading {selectedFile?.name}...</Typography>
                  </Box>
                ) : (
                  <>
                    <UploadIcon sx={{ fontSize: 40, mb: 1 }} />
                    {selectedFile ? (
                      <Typography>
                        Selected: {selectedFile.name}
                      </Typography>
                    ) : (
                      <Typography>
                        {isDragActive
                          ? 'Drop the PDF here'
                          : 'Drag & drop a PDF file here, or click to select'}
                      </Typography>
                    )}
                  </>
                )}
              </Box>
            ) : (
              <TextField
                fullWidth
                multiline
                rows={4}
                label="LaTeX Template"
                value={template}
                onChange={(e) => setTemplate(e.target.value)}
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={
              isUploading || !name || (inputMethod === 'latex' ? !template : !selectedFile)
            }
          >
            {isUploading ? 'Creating...' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default ProblemSets;
