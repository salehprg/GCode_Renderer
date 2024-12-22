import React, { useState } from 'react';
import logo from './logo.svg';
import './App.css';
import {
  Box,
  TextField,
  Button,
  RadioGroup,
  FormControlLabel,
  Radio,
  Typography,
  Checkbox,
  CircularProgress,
} from "@mui/material";
import axios from 'axios';

declare global {
  interface Window {
    electron: {
      openFolder: () => Promise<string | undefined>;
    };
  }
}

function App() {
  const [formState, setFormState] = useState({
    inputImagesFolder: "",
    referenceImagesFolder: "",
    maskImagesFolder: "",
    sampleCount: 0,
    inputImagesFolder_count: 0,
    referenceImagesFolder_count: 0,
    maskImagesFolder_count: 0,
    featureExtraction: {
      Block1: false,
      Block2: false,
      Block3: false,
    },
    maskExpansionRadius: 6,
    defectScoreThreshold: 128,
    defectAreaThreshold: 500,
    alarmTriggerCount: 5,
  });
  const [loading, setLoading] = useState(false)
  const [videos, setVideos] = useState({
    videos_score_map: "",
    videos_result_mask: "",
    videos_final: "",
  })

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const response = await axios.post("http://127.0.0.1:8000/submit-form", formState, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("Form submission success:", response.data);

      setVideos(response.data)
    } catch (error) {
      if (axios.isAxiosError(error)) {
        alert(error.response?.data.detail)
        console.error("Axios error:", error.response?.data || error.message);
      } else {
        console.error("Unexpected error:", error);
      }
    }
    finally {
      setLoading(false)
    }
  };

  const handleImageCount = async (key: string, folderPath: string) => {
    setLoading(true)
    try {
      const response = await axios.get(`http://127.0.0.1:8000/count-images?folder_path=${folderPath}`, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      setFormState(prevState => (
        {
          ...prevState,
          [`${key}_count`]: response.data.images_count
        }
      ))
      console.log("Form submission success:", response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        alert(error.response?.data.detail)
        console.error("Axios error:", error.response?.data || error.message);
      } else {
        console.error("Unexpected error:", error);
      }
    }
    finally {
      setLoading(false)
    }
  };

  // Handler for file selection
  const handleFileSelect = async (key: string) => {
    console.log(window.electron)
    const selectedPath = await window.electron.openFolder();

    handleImageCount(key, selectedPath ?? "")
    setFormState((prevState) => ({
      ...prevState,
      [key]: selectedPath, // Store the folder path
    }));
  };

  // Handler for input changes
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;

    let number = parseFloat(value)
    if (name == "defectScoreThreshold") {
      if (number < 0)
        number = 0
      if (number > 256)
        number = 256
    }

    setFormState((prevState) => ({
      ...prevState,
      [name]: number,
    }));
  };

  // Handler for radio button change
  const handleCheckboxChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = event.target;
    setFormState((prevState) => ({
      ...prevState,
      featureExtraction: {
        ...prevState.featureExtraction,
        [name]: checked,
      },
    }));
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
        p: 3,
        margin: "auto",
      }}
    >
      {/* Input Folders Section */}
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <TextField
          fullWidth
          label="Input Images Folder"
          variant="outlined"
          size="small"
          value={formState.inputImagesFolder}
          InputProps={{ readOnly: true }}
        />
        <Button
          variant="contained"
          onClick={() => handleFileSelect("inputImagesFolder")}
        >
          Browse
        </Button>
      </Box>
      <Typography sx={{ marginLeft: 2, marginBottom: 1 }} fontSize={12}>Images count {formState.inputImagesFolder_count}</Typography>
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <TextField
          fullWidth
          label="Reference Images Folder"
          variant="outlined"
          size="small"
          value={formState.referenceImagesFolder}
          InputProps={{ readOnly: true }}
        />
        <Button
          variant="contained"
          onClick={() => handleFileSelect("referenceImagesFolder")}
        >
          Browse
        </Button>
      </Box>
      <Typography sx={{ marginLeft: 2, marginBottom: 1 }} fontSize={12}>Images count {formState.referenceImagesFolder_count}</Typography>
      <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
        <TextField
          fullWidth
          label="Mask Images Folder"
          variant="outlined"
          size="small"
          value={formState.maskImagesFolder}
          InputProps={{ readOnly: true }}
        />
        <Button
          variant="contained"
          onClick={() => handleFileSelect("maskImagesFolder")}
        >
          Browse
        </Button>
      </Box>
      <Typography sx={{ marginLeft: 2, marginBottom: 1 }} fontSize={12}>Images count {formState.maskImagesFolder_count}</Typography>

      <TextField
        label="Sample Count"
        type="number"
        name="sampleCount"
        value={formState.sampleCount}
        onChange={handleInputChange}
        size="small"
        helperText={<span style={{color:'red', fontStyle:'italic'}}>0 Means all images will process</span>}
      />

      {/* Settings Section */}
      <Box
        sx={{
          border: "1px solid black",
          borderRadius: 2,
          p: 2,
          mt: 2,
          display: "flex",
          flexDirection: "column",
          gap: 2,
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: "bold" }}>
          Settings
        </Typography>

        {/* Feature Extraction Section */}
        <Typography>Feature Extraction (ResNet18)</Typography>
        <Box display="flex" flexDirection="row" gap={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.featureExtraction.Block1}
                onChange={handleCheckboxChange}
                name="Block1"
              />
            }
            label="Block1"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.featureExtraction.Block2}
                onChange={handleCheckboxChange}
                name="Block2"
              />
            }
            label="Block2"
          />
          <FormControlLabel
            control={
              <Checkbox
                checked={formState.featureExtraction.Block3}
                onChange={handleCheckboxChange}
                name="Block3"
              />
            }
            label="Block3"
          />
        </Box>

        {/* Thresholds and Parameters */}
        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
          <TextField
            label="Mask Expansion Radius"
            type="number"
            name="maskExpansionRadius"
            value={formState.maskExpansionRadius}
            onChange={handleInputChange}
            InputProps={{ endAdornment: <span>Pixel</span> }}
            size="small"
          />
          <TextField
            label="Defect Score Threshold"
            type="number"
            name="defectScoreThreshold"
            value={formState.defectScoreThreshold}
            onChange={handleInputChange}
            size="small"
          />
          <TextField
            label="Defect Area Threshold"
            type="number"
            name="defectAreaThreshold"
            value={formState.defectAreaThreshold}
            onChange={handleInputChange}
            InputProps={{ endAdornment: <span>Pixel</span> }}
            size="small"
          />
          <TextField
            label="Alarm Trigger Count"
            type="number"
            name="alarmTriggerCount"
            value={formState.alarmTriggerCount}
            onChange={handleInputChange}
            size="small"
          />
        </Box>
      </Box>
      {(!loading && videos.videos_final !== '') && <Box sx={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* <TextField size='small' disabled label="Mask Video" value={videos.videos_result_mask} />
        <TextField size='small' disabled label="Score Video" value={videos.videos_score_map} />
        <TextField size='small' disabled label="Final Video" value={videos.videos_final} /> */}
        <a href={videos.videos_result_mask} download>Mask Video</a>
        <a href={videos.videos_score_map} download>Score Map Video</a>
        <a href={videos.videos_final} download>Final Video</a>
      </Box>}
      <Button
        variant="contained"
        disabled={loading}
        onClick={() => handleSubmit()}
      >
        {loading ? <CircularProgress /> : "Submit"}
      </Button>
    </Box>
  );
}

export default App;
