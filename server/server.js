const express = require('express');
const multer = require('multer');
const streamifier = require('streamifier');
const cloudinary = require('./cloudinary');
const cors = require('cors');
const axios = require('axios');

const app = express();
const upload = multer();
app.use(cors());
app.use(express.json());

app.post('/receive-signal-from-ai-pipeline', (req, res) => {
  const analysisData = req.body;
  console.log('📬 Received analysis result from FastAPI:', analysisData);

  // You can store it, emit to frontend via socket, or trigger alerts here

  res.json({ status: 'received' });
});

app.post('/upload', upload.single('pdf'), async (req, res) => {
  try {
    const userId = req.body.userId;

    const stream = cloudinary.uploader.upload_stream(
      {
        resource_type: 'raw',
        folder: 'pdf_uploads',
        public_id: req.file.originalname.split('.')[0],
      },
      async (error, result) => {
        if (error) {
          console.error(error);
          return res.status(500).json({ error: 'Cloudinary upload failed' });
        }

        const downloadUrl = result.secure_url;
        try{
          //creating metadata for the pipelineing server
          const userId = req.body.userId;
          const subject = req.body.subject;
          const assignmentId = req.body.assignmentId;
          const userName = req.body['user-name'];
          console.log('Receieved data from frontend => ', { userId, subject, assignmentId, userName }); 
          // sending metadata to ai-pipeline
          try {
            await axios.post('http://127.0.0.1:7000/process', {
              userId: userId,
              fileUrl: downloadUrl,
              filename: req.file.originalname,
              subject: subject,
              assignmentId: assignmentId,
              userName: userName,
              strict_ai_detection:true,
              use_top_features:true
            });
            console.log('Metadata sent to FastAPI successfully');
          } catch (fastapiError) {
            console.error('Error sending to FastAPI:', fastapiError.message);
          }
        }catch(err){
          console.error('Error getting field"s', err);
          return res.status(500).json({ error: err.message });
        }

        res.json({ downloadUrl });
      }
    );

    streamifier.createReadStream(req.file.buffer).pipe(stream);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/files', async (req, res) => {
  try {
    const result = await cloudinary.api.resources({
      type: 'upload',
      resource_type: 'raw',
      prefix: 'pdf_uploads/',
      max_results: 10,
    });

    const urls = result.resources.map(file => file.secure_url);
    res.json({ files: urls });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch files' });
  }
});

const PORT = 3900;
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
