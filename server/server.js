const express = require('express');
const multer = require('multer');
const streamifier = require('streamifier');
const cloudinary = require('./cloudinary');
const cors = require('cors');
const axios = require('axios');
const { MongoClient } = require('mongodb');


const app = express();
const upload = multer();
app.use(cors());
app.use(express.json());

// MongoDB connection
const MONGODB_URI = 'mongodb+srv://sambhranta1123:SbGgIK3dZBn9uc2r@cluster0.jjcc5or.mongodb.net/';
const DATABASE_NAME = 'certimint';
const COLLECTION_NAME = 'assignments';

let db;

// Connect to MongoDB
MongoClient.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(client => {
  console.log('✅ Connected to MongoDB');
  db = client.db(DATABASE_NAME);
})
.catch(error => {
  console.error('❌ MongoDB connection error:', error);
});

const reviewedAssignments = [];

app.get('/api/assignments', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;

    const collection = db.collection(COLLECTION_NAME);
    
    // Get total count
    const totalCount = await collection.countDocuments();
    // Get paginated assignments
    const assignments = await collection
      .find({})
      .sort({ upload_timestamp: -1 }) // Sort by newest first
      .skip(skip)
      .limit(limit)
      .toArray();

    res.json({
      success: true,
      data: assignments,
      pagination: {
        currentPage: page,
        totalPages: Math.ceil(totalCount / limit),
        totalItems: totalCount,
        itemsPerPage: limit,
        hasNextPage: page < Math.ceil(totalCount / limit),
        hasPrevPage: page > 1
      }
    });
  } catch (error) {
    console.error('Error fetching assignments:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch assignments',
      message: error.message 
    });
  }
});

// Get assignments by username
app.get('/api/assignments/user/:username', async (req, res) => {
  try {
    const { username } = req.params;
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const skip = (page - 1) * limit;

    const collection = db.collection(COLLECTION_NAME);
    
    // Get total count for this user
    const totalCount = await collection.countDocuments({ username: username });
    
    // Get paginated assignments for this user
    const assignments = await collection
      .find({ username: username })
      .sort({ upload_timestamp: -1 })
      .skip(skip)
      .limit(limit)
      .toArray();

    res.json({
      success: true,
      data: assignments,
      username: username,
      pagination: {
        currentPage: page,
        totalPages: Math.ceil(totalCount / limit),
        totalItems: totalCount,
        itemsPerPage: limit,
        hasNextPage: page < Math.ceil(totalCount / limit),
        hasPrevPage: page > 1
      }
    });
  } catch (error) {
    console.error('Error fetching user assignments:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch user assignments',
      message: error.message 
    });
  }
});

// Get single assignment by ID
app.get('/api/assignments/id/:assignmentId', async (req, res) => {
  try {
    const { assignmentId } = req.params;
    const collection = db.collection(COLLECTION_NAME);
    
    const assignment = await collection.findOne({ assignment_id: assignmentId });
    
    if (!assignment) {
      return res.status(404).json({ 
        success: false, 
        error: 'Assignment not found' 
      });
    }

    res.json({
      success: true,
      data: assignment
    });
  } catch (error) {
    console.error('Error fetching assignment:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch assignment',
      message: error.message 
    });
  }
});

// Get assignment statistics
app.get('/api/assignments/stats', async (req, res) => {
  try {
    const collection = db.collection(COLLECTION_NAME);
    
    // Get basic stats
    const totalAssignments = await collection.countDocuments();
    const passedAssignments = await collection.countDocuments({ status: 'PASSED' });
    const failedAssignments = await collection.countDocuments({ status: 'FAILED' });
    const pendingAssignments = await collection.countDocuments({ status: 'PENDING' });
    
    // Get AI detection stats
    const aiDetectedAssignments = await collection.countDocuments({ 
      'ai_detection.ai_patterns_detected': true 
    });
    
    // Get plagiarism stats
    const plagiarismDetectedAssignments = await collection.countDocuments({ 
      'plagiarism_check.plagiarism_detected': true 
    });

    // Get subject distribution
    const subjectStats = await collection.aggregate([
      { $group: { _id: '$subject', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]).toArray();
    // Get monthly submissions (last 12 months)
    const monthlyStats = await collection.aggregate([
      {
        $match: {
          upload_timestamp: {
            $gte: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString()
          }
        }
      },
      {
        $group: {
          _id: {
            year: { $year: { $dateFromString: { dateString: '$upload_timestamp' } } },
            month: { $month: { $dateFromString: { dateString: '$upload_timestamp' } } }
          },
          count: { $sum: 1 }
        }
      },
      { $sort: { '_id.year': 1, '_id.month': 1 } }
    ]).toArray();
    res.json({
      success: true,
      stats: {
        total: totalAssignments,
        passed: passedAssignments,
        failed: failedAssignments,
        pending: pendingAssignments,
        aiDetected: aiDetectedAssignments,
        plagiarismDetected: plagiarismDetectedAssignments
      },
      subjectDistribution: subjectStats.map(item => ({
        subject: item._id,
        count: item.count
      })),
      monthlySubmissions: monthlyStats.map(item => ({
        year: item._id.year,
        month: item._id.month,
        monthName: new Date(item._id.year, item._id.month - 1).toLocaleDateString('en-US', { month: 'short' }),
        count: item.count
      }))
    });
  } catch (error) {
    console.error('Error fetching assignment stats:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch assignment statistics',
      message: error.message 
    });
  }
});

// Get user-specific statistics
app.get('/api/assignments/stats/user/:username', async (req, res) => {
  try {
    const { username } = req.params;
    const collection = db.collection(COLLECTION_NAME);
    
    // Get user-specific stats
    const totalAssignments = await collection.countDocuments({ username });
    const passedAssignments = await collection.countDocuments({ username, status: 'PASSED' });
    const failedAssignments = await collection.countDocuments({ username, status: 'FAILED' });
    const pendingAssignments = await collection.countDocuments({ username, status: 'PENDING' });
    
    const aiDetectedAssignments = await collection.countDocuments({ 
      username,
      'ai_detection.ai_patterns_detected': true 
    });
    
    const plagiarismDetectedAssignments = await collection.countDocuments({ 
      username,
      'plagiarism_check.plagiarism_detected': true 
    });

    // Get user's subject distribution
    const subjectStats = await collection.aggregate([
      { $match: { username } },
      { $group: { _id: '$subject', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]).toArray();

    res.json({
      success: true,
      username,
      stats: {
        total: totalAssignments,
        passed: passedAssignments,
        failed: failedAssignments,
        pending: pendingAssignments,
        aiDetected: aiDetectedAssignments,
        plagiarismDetected: plagiarismDetectedAssignments
      },
      subjectDistribution: subjectStats.map(item => ({
        subject: item._id,
        count: item.count
      }))
    });
    } catch (error) {
    console.error('Error fetching user assignment stats:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to fetch user assignment statistics',
      message: error.message 
    });
  }
});

// Search assignments
app.get('/api/assignments/search', async (req, res) => {
  try {
    const { 
      query, 
      subject, 
      status, 
      username,
      page = 1, 
      limit = 10 
    } = req.query;
    
    const skip = (parseInt(page) - 1) * parseInt(limit);
    const collection = db.collection(COLLECTION_NAME);
    
    // Build search filter
    const filter = {};
    
    if (query) {
      filter.$or = [
        { assignment_id: { $regex: query, $options: 'i' } },
        { subject: { $regex: query, $options: 'i' } },
        { username: { $regex: query, $options: 'i' } }
      ];
    }
    if (subject) filter.subject = subject;
    if (status) filter.status = status;
    if (username) filter.username = username;

    const totalCount = await collection.countDocuments(filter);
    const assignments = await collection
      .find(filter)
      .sort({ upload_timestamp: -1 })
      .skip(skip)
      .limit(parseInt(limit))
      .toArray();

    res.json({
      success: true,
      data: assignments,
      pagination: {
        currentPage: parseInt(page),
        totalPages: Math.ceil(totalCount / parseInt(limit)),
        totalItems: totalCount,
        itemsPerPage: parseInt(limit),
        hasNextPage: parseInt(page) < Math.ceil(totalCount / parseInt(limit)),
        hasPrevPage: parseInt(page) > 1
      }
    });
    } catch (error) {
    console.error('Error searching assignments:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Failed to search assignments',
      message: error.message 
    });
  }
});


app.post('/receive-signal-from-ai-pipeline', (req, res) => {
  const analysisData = req.body;
  console.log('📬 Received analysis result from FastAPI:', analysisData);

  // You can store it, emit to frontend via socket, or trigger alerts here
  // Extract the required information from the analysis data
  const { userId, assignmentId, status, feedback } = analysisData;
  reviewedAssignments.push({
    userId,
    assignmentId,
    status,
    feedback,
    timestamp: Date.now()
  });

  setTimeout(() => {
    const index = reviewedAssignments.findIndex(
      r => r.userId === userId && r.assignmentId === assignmentId
    );
    if (index > -1){
      reviewedAssignments.splice(index, 1);
      console.log(`📬 Removed old analysis result for user ${userId} and assignment ${assignmentId}`);
    }
  }, 300000); // remove after 5 minutes
  
  res.json({ status: 'received' });
});

app.get('/reviewed-assignments/:userId', (req, res) => {
  const { userId } = req.params;
  const results = reviewedAssignments.filter(r => r.userId === userId);
  res.json(results);
});

app.get('/notifications/:userId', (req, res) => {
  const { userId } = req.params;
  const notifications = reviewedAssignments.filter(n => n.userId === userId);
  res.json(notifications);
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
        console.log(`📁 File "${req.file.originalname}" successfully uploaded to cloud storage - URL: ${downloadUrl}`);
        
        // Send success response immediately after Cloudinary upload completes
        // This will trigger the frontend toast while the server continues processing
        res.json({ 
          downloadUrl,
          success: true,
          message: 'Your Assignment has been uploaded successfully and is being processed.',
        });
        
        try{
          //creating metadata for the pipelineing server
          const userId = req.body.userId;
          const subject = req.body.subject;
          const assignmentId = req.body.assignmentId;
          const userName = req.body['user-name'];
          console.log('Receieved data from frontend => ', { userId, subject, assignmentId, userName }); 
          // sending metadata to ai-pipeline
          try {
            await axios.post('https://fdb3-14-194-180-252.ngrok-free.app/process', {
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
