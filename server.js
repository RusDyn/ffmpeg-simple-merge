const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Main merge endpoint
app.post('/merge', async (req, res) => {
  const { videoUrl, audioUrl } = req.body;
  
  if (!videoUrl || !audioUrl) {
    return res.status(400).json({ 
      error: 'Both videoUrl and audioUrl are required' 
    });
  }
  
  const jobId = uuidv4();
  const outputPath = `/tmp/output_${jobId}.mp4`;
  
  try {
    console.log(`Starting merge job ${jobId}`);
    console.log(`Video: ${videoUrl}`);
    console.log(`Audio: ${audioUrl}`);
    
    // FFmpeg command with HTTP protocol enabled and proper video scaling
    const ffmpegArgs = [
      '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
      '-i', videoUrl,
      '-i', audioUrl,
      '-c:v', 'libx264',  // Re-encode video to allow scaling
      '-c:a', 'aac',
      '-map', '0:v:0',
      '-map', '1:a:0',
      '-filter_complex', '[0:v]scale2ref=oh*mdar:ih[v][ref];[v]setpts=PTS*TDUR/VDUR[vout]',
      '-filter:a', 'aresample=44100',
      '-shortest',  // Match shortest stream duration
      '-y',  // Overwrite output file
      outputPath
    ];
    
    const ffmpeg = spawn('ffmpeg', ffmpegArgs);
    
    let stderr = '';
    ffmpeg.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    ffmpeg.on('close', (code) => {
      if (code === 0) {
        console.log(`Job ${jobId} completed successfully`);
        
        // Read the output file and send as response
        fs.readFile(outputPath, (err, data) => {
          if (err) {
            console.error(`Error reading output file: ${err}`);
            return res.status(500).json({ error: 'Failed to read output file' });
          }
          
          // Clean up temp file
          fs.unlink(outputPath, (unlinkErr) => {
            if (unlinkErr) console.warn(`Failed to delete temp file: ${unlinkErr}`);
          });
          
          // Send file as binary response
          res.set({
            'Content-Type': 'video/mp4',
            'Content-Disposition': `attachment; filename="merged_${jobId}.mp4"`,
            'Content-Length': data.length
          });
          res.send(data);
        });
      } else {
        console.error(`FFmpeg failed with code ${code}`);
        console.error(`FFmpeg stderr: ${stderr}`);
        
        // Clean up temp file on error
        if (fs.existsSync(outputPath)) {
          fs.unlink(outputPath, (unlinkErr) => {
            if (unlinkErr) console.warn(`Failed to delete temp file: ${unlinkErr}`);
          });
        }
        
        res.status(500).json({ 
          error: 'Video processing failed',
          details: stderr.slice(-500) // Last 500 chars of error
        });
      }
    });
    
    ffmpeg.on('error', (error) => {
      console.error(`FFmpeg process error: ${error}`);
      res.status(500).json({ error: 'FFmpeg process failed to start' });
    });
    
  } catch (error) {
    console.error(`Job ${jobId} error:`, error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Alternative endpoint that returns a download URL (if you prefer async processing)
app.post('/merge-async', async (req, res) => {
  const { videoUrl, audioUrl } = req.body;
  
  if (!videoUrl || !audioUrl) {
    return res.status(400).json({ 
      error: 'Both videoUrl and audioUrl are required' 
    });
  }
  
  const jobId = uuidv4();
  res.json({ 
    jobId, 
    message: 'Processing started',
    statusUrl: `/status/${jobId}`,
    downloadUrl: `/download/${jobId}`
  });
  
  // Process in background (implement if needed)
  processVideoAsync(jobId, videoUrl, audioUrl);
});

async function processVideoAsync(jobId, videoUrl, audioUrl) {
  // Similar to above but store result and provide status endpoint
  // Implementation depends on your needs
}

app.listen(PORT, () => {
  console.log(`Video merger API running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Merge endpoint: POST http://localhost:${PORT}/merge`);
});