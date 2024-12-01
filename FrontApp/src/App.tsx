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
} from "@mui/material";
import axios from 'axios';

function App() {
  const [formState, setFormState] = useState({
    inputImagesFolder: "",
    referenceImagesFolder: "",
    maskImagesFolder: "",
    featureExtraction: {
      Block1: false,
      Block2: false,
      Block3: false,
    },
    maskExpansionRadius: 6,
    defectScoreThreshold: 750,
    defectAreaThreshold: 900,
    alarmTriggerCount: 5,
  });

  const handleSubmit = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/submit-form", formState, {
        headers: {
          "Content-Type": "application/json",
        },
      });

      console.log("Form submission success:", response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        alert(error.response?.data.detail)
        console.error("Axios error:", error.response?.data || error.message);
      } else {
        console.error("Unexpected error:", error);
      }
    }
  };

  // Handler for file selection
  const handleFileSelect = (key: string) => {

    if (window.electronAPI) {
      window.electronAPI.selectFolder().then(folderPaths => {
        if (folderPaths.length > 0) {
          console.log('Selected folder:', folderPaths[0]);
          alert(`You selected: ${folderPaths[0]}`);
        } else {
          console.log('No folder selected.');
        }
      });
    }
    // const input = document.createElement("input");
    // input.type = "file";
    // input.webkitdirectory = true; // Allows folder selection
    // input.onchange = (e) => {
    //   const file = (e.target as HTMLInputElement).files?.[0];
    //   if (file) {
    //     setFormState((prevState) => ({
    //       ...prevState,
    //       [key]: file.webkitRelativePath.split("/")[0], // Store the folder path
    //     }));
    //   }
    // };
    // input.click();
  };

  // Handler for input changes
  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormState((prevState) => ({
      ...prevState,
      [name]: parseFloat(value),
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
        gap: 2,
        p: 3,
        border: "1px solid black",
        width: "600px",
        margin: "auto",
        borderRadius: 2,
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
      <Button
        variant="contained"
        onClick={() => handleSubmit()}
      >
        Submit
      </Button>
    </Box>
  );
}

export default App;
