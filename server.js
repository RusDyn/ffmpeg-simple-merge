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

// Helper function to get media duration
function getMediaDuration(url) {
  return new Promise((resolve, reject) => {
    const ffprobe = spawn('ffprobe', [
      '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
      '-v', 'quiet',
      '-show_entries', 'format=duration',
      '-of', 'csv=p=0',
      url
    ]);
    
    let stdout = '';
    let stderr = '';
    
    ffprobe.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    ffprobe.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    ffprobe.on('close', (code) => {
      if (code === 0) {
        const duration = parseFloat(stdout.trim());
        if (isNaN(duration)) {
          reject(new Error('Invalid duration format'));
        } else {
          resolve(duration);
        }
      } else {
        reject(new Error(`ffprobe failed: ${stderr}`));
      }
    });
  });
}

// Main merge endpoint
app.post('/merge', async (req, res) => {
  const { videoUrl, audioUrl } = req.body;
  
  if (!videoUrl || !audioUrl) {
    return res.status(400).json({ 
      error: 'Both videoUrl and audioUrl are required' 
    });
  }
  
  // Validate URLs
  try {
    new URL(videoUrl);
    new URL(audioUrl);
  } catch (error) {
    return res.status(400).json({ 
      error: 'Invalid URL format' 
    });
  }
  
  const jobId = uuidv4();
  const outputPath = `/tmp/output_${jobId}.mp4`;
  
  try {
    console.log(`Starting merge job ${jobId}`);
    console.log(`Video: ${videoUrl}`);
    console.log(`Audio: ${audioUrl}`);
    
    // Get durations of both files
    console.log('Getting video duration...');
    const videoDuration = await getMediaDuration(videoUrl);
    console.log(`Video duration: ${videoDuration}s`);
    
    console.log('Getting audio duration...');
    const audioDuration = await getMediaDuration(audioUrl);
    console.log(`Audio duration: ${audioDuration}s`);
    
    const finalDuration = Math.max(videoDuration, audioDuration);
    console.log(`Final output duration will be: ${finalDuration}s`);
    
    // Determine processing strategy based on which is longer
    let ffmpegArgs;
    
    if (audioDuration >= videoDuration) {
      // Audio is longer or equal - slow down video to match audio duration
      const speedFactor = videoDuration / audioDuration;
      console.log(`Audio is longer. Slowing down video with factor: ${speedFactor}`);
      
      ffmpegArgs = [
        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
        '-i', videoUrl,
        '-i', audioUrl,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-filter_complex', `[0:v]setpts=PTS*${1/speedFactor}[slowvideo];[0:a]atempo=${speedFactor}[slowaudio];[slowaudio][1:a]amix=inputs=2:duration=longest[mixedaudio]`,
        '-map', '[slowvideo]',
        '-map', '[mixedaudio]',
        '-preset', 'fast',
        '-crf', '23',
        '-t', audioDuration,  // Output duration = audio duration
        '-y',
        outputPath
      ];
    } else {
      // Video is longer - keep video speed, mix original video audio with new audio
      console.log(`Video is longer. Keeping video speed, mixing audio tracks`);
      
      ffmpegArgs = [
        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',
        '-i', videoUrl,
        '-i', audioUrl,
        '-c:v', 'copy',  // Copy video without re-encoding (faster)
        '-c:a', 'aac',
        '-filter_complex', `[0:a][1:a]amix=inputs=2:duration=first[mixedaudio]`,
        '-map', '0:v:0',
        '-map', '[mixedaudio]',
        '-t', videoDuration,  // Output duration = video duration
        '-y',
        outputPath
      ];
    }
    
    console.log('Starting FFmpeg processing...');
    const ffmpeg = spawn('ffmpeg', ffmpegArgs);
    
    let stderr = '';
    ffmpeg.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    ffmpeg.on('close', (code) => {
      if (code === 0) {
        console.log(`Job ${jobId} completed successfully`);
        
        // Check if output file exists and has content
        if (!fs.existsSync(outputPath)) {
          return res.status(500).json({ error: 'Output file was not created' });
        }
        
        const stats = fs.statSync(outputPath);
        if (stats.size === 0) {
          fs.unlink(outputPath, () => {});
          return res.status(500).json({ error: 'Output file is empty' });
        }
        
        console.log(`Output file size: ${stats.size} bytes`);
        
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
    
    // Clean up any temp files
    if (fs.existsSync(outputPath)) {
      fs.unlink(outputPath, () => {});
    }
    
    if (error.message.includes('ffprobe failed')) {
      res.status(400).json({ 
        error: 'Failed to analyze media files. Please check URLs are valid and accessible.',
        details: error.message
      });
    } else {
      res.status(500).json({ 
        error: 'Internal server error',
        details: error.message
      });
    }
  }
});

app.listen(PORT, () => {
  console.log(`Video merger API running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`Merge endpoint: POST http://localhost:${PORT}/merge`);
});