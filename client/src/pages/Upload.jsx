import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Upload.css';
import { IoMdArrowRoundBack } from "react-icons/io";
import { BiLogOut } from "react-icons/bi";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

export default function Upload() {
  // Add a new state for tracking upload processing
  const [isUploading, setIsUploading] = useState(false);
  
  // All your existing state variables remain the same
  const [file, setFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  const [isDragging, setIsDragging] = useState(false);
  const [subject, setSubject] = useState('');
  const [selectedAssignment, setSelectedAssignment] = useState('');
  const [assignments, setAssignments] = useState([
    { id: 1, name: 'Ass-1', status: 'Submitted' },
    { id: 2, name: 'Ass-2', status: 'Pending' },
    { id: 3, name: 'Ass-3', status: 'Not Submitted' },
    { id: 4, name: 'Ass-4', status: 'Not Submitted' },
    { id: 5, name: 'Ass-5', status: 'Not Submitted' },
    { id: 6, name: 'Ass-6', status: 'Not Submitted' },
    { id: 7, name: 'Ass-7', status: 'Not Submitted' },
    { id: 8, name: 'Ass-8', status: 'Not Submitted' },
    { id: 9, name: 'Ass-9', status: 'Not Submitted' },
    { id: 10, name: 'Ass-10', status: 'Not Submitted' },
  ]);
  
  // Initialize states from localStorage if available
  const [uploadSuccessful, setUploadSuccessful] = useState(() => {
    const saved = localStorage.getItem('uploadSuccessful');
    return saved ? JSON.parse(saved) : false;
  });
  
  // Initialize cooldownTime first
  const [cooldownTime, setCooldownTime] = useState(() => {
    const saved = localStorage.getItem('cooldownTime');
    const savedTime = saved ? parseInt(saved) : 0;
    
    // Check if the timer should still be active based on the end time
    const endTime = localStorage.getItem('cooldownEndTime');
    if (endTime) {
      const remainingTime = Math.floor((parseInt(endTime) - Date.now()) / 1000);
      return remainingTime > 0 ? remainingTime : 0;
    }
    
    return savedTime;
  });
  
  // Then initialize isButtonLocked based on cooldownTime
  const [isButtonLocked, setIsButtonLocked] = useState(() => {
    return cooldownTime > 0;
  });
  
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('uploadSuccessful', JSON.stringify(uploadSuccessful));
  }, [uploadSuccessful]);
  
  useEffect(() => {
    localStorage.setItem('cooldownTime', cooldownTime.toString());
    
    // Save the expected end time as well for refresh persistence
    if (cooldownTime > 0) {
      const endTime = Date.now() + (cooldownTime * 1000);
      localStorage.setItem('cooldownEndTime', endTime.toString());
    } else {
      localStorage.removeItem('cooldownEndTime');
    }
  }, [cooldownTime]);

  // Timer countdown effect
  useEffect(() => {
    let interval = null;
    
    if (cooldownTime > 0) {
      interval = setInterval(() => {
        setCooldownTime(prevTime => {
          const newTime = prevTime - 1;
          if (newTime <= 0) {
            clearInterval(interval);
            setIsButtonLocked(false);
            return 0;
          }
          return newTime;
        });
      }, 1000);
    } else if (cooldownTime === 0 && isButtonLocked) {
      setIsButtonLocked(false);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [cooldownTime, isButtonLocked]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const getPendingAssignments = () => {
    return assignments.filter(assignment => 
      assignment.status !== 'Submitted' && assignment.status !== 'Pending'
    );
  };

  const handleUpload = async () => {
    if (!file || !user || !selectedAssignment) {
      toast.error('Please select an assignment and a file to upload');
      return;
    }

    if (!subject.trim()) {
      toast.error('Please enter a subject name');
      return;
    }

    // Set uploading state to true to show animation
    setIsUploading(true);

    const formData = new FormData();
    formData.append('user-name', user.name);
    formData.append('pdf', file);
    formData.append('userId', user.id);
    formData.append('assignmentId', selectedAssignment);
    formData.append('subject', subject);

    try {
      const res = await axios.post('http://localhost:3900/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress({
            ...uploadProgress,
            [file.name]: percentCompleted
          });
        }
      });
      
      // Update the assignment status to "Pending" instead of "Submitted"
      const updatedAssignments = assignments.map(assignment => {
        if (assignment.id === parseInt(selectedAssignment)) {
          return { ...assignment, status: 'Pending' };
        }
        return assignment;
      });
      
      setAssignments(updatedAssignments);
      setUploadSuccessful(true);
      
      // Set the cooldown timer to 5 minutes (300 seconds) and lock the button
      setCooldownTime(10);
      setIsButtonLocked(true);
      
      toast.success('Assignment uploaded successfully!');
      setFile(null);
      setSelectedAssignment('');
      
      // Clear the progress after successful upload
      const newProgress = {...uploadProgress};
      if (file) {
        delete newProgress[file.name];
        setUploadProgress(newProgress);
      }
      
      // Save the updated assignments to localStorage
      localStorage.setItem('assignments', JSON.stringify(updatedAssignments));
      console.log("sending data to server",res);
      
    } catch (err) {
      console.error(err);
      toast.error('Upload failed. Please try again.');
    } finally {
      // Always set uploading state to false when done
      setIsUploading(false);
    }
  };

  // Function to format the remaining time
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
  };

  // Load assignments from localStorage on initial render
  useEffect(() => {
    const savedAssignments = localStorage.getItem('assignments');
    if (savedAssignments) {
      setAssignments(JSON.parse(savedAssignments));
    }
  }, []);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      // Add to progress tracking
      setUploadProgress({
        ...uploadProgress,
        [e.dataTransfer.files[0].name]: 0
      });
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      // Add to progress tracking
      setUploadProgress({
        ...uploadProgress,
        [e.target.files[0].name]: 0
      });
    }
  };

  const handleCancel = () => {
    setFile(null);
    setSelectedAssignment('');
    const newProgress = {...uploadProgress};
    Object.keys(newProgress).forEach(key => delete newProgress[key]);
    setUploadProgress(newProgress);
  };

  // Rest of your component remains the same
  return (
    <div className="dashboard-container">
      {/* The UI code remains the same */}
      <ToastContainer theme="dark" position="top-right" />
      
      <div className="header">
        <div className="user-profile">
          {user?.picture ? (
            <img 
              src={user.picture} 
              alt="Profile" 
              className="profile-image" 
            />
          ) : (
            <div className="profile-placeholder">
              {user?.name?.charAt(0) || 'S'}
            </div>
          )}
          <h1>Hi, {user?.name || 'Student'}</h1>
        </div>
        <div className="header-right">
          <button className="back-btn"><IoMdArrowRoundBack style={{verticalAlign:'middle'}} size={20}/> Back</button>
          <button className="logout-btn" onClick={handleLogout}>
            <BiLogOut style={{verticalAlign:'middle',marginRight:'7px'}} size={20} />
            Logout
            </button>
        </div>
      </div>
      
      <div className="dashboard-content">
        {/* Left panel remains the same */}
        <div className="left-panel">
          <div className="assignment-counter">
            Total Assignments - {assignments.length}
          </div>
          
          <div className="subject-input">
            <label>Subject Name</label>
            <input 
              type="text" 
              placeholder="Name Here" 
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>
          
          <div className="assignment-selection">
            <label>Select your assignment</label>
            <select 
              value={selectedAssignment} 
              onChange={(e) => setSelectedAssignment(e.target.value)}
            >
              <option value="">Select Assignment</option>
              {getPendingAssignments().map(assignment => (
                <option key={assignment.id} value={assignment.id}>
                  Assignment - {assignment.id}
                </option>
              ))}
            </select>
          </div>
          
          <div className="assignments-table">
            <div className="table-header">
              <div className="table-column">Assignments</div>
              <div className="table-column">Status</div>
            </div>
            <div className="table-body">
              {assignments.map(assignment => (
                <div className="table-row" key={assignment.id}>
                  <div className="table-column">Assignment - {assignment.id}</div>
                  <div className={`table-column status status-${assignment.status.toLowerCase().replace(' ', '-')}`}>
                    {assignment.status}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <div className="right-panel">
          {/* Right panel with conditional rendering */}
          {!uploadSuccessful ? (
            <div className="upload-section">
              {/* Upload section remains the same */}
              <div 
                className={`drop-area ${isDragging ? 'dragging' : ''} ${!selectedAssignment ? 'disabled' : ''}`}
                onDragOver={selectedAssignment ? handleDragOver : e => e.preventDefault()}
                onDragLeave={handleDragLeave}
                onDrop={selectedAssignment ? handleDrop : e => e.preventDefault()}
              >
                <div className="drop-icon">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 16L12 8" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M9 11L12 8L15 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <path d="M8 16H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                </div>
                {!selectedAssignment ? (
                  <p>Please select an assignment first</p>
                ) : (
                  <>
                    <p>Drag & drop or <label className="choose-file">Choose file<input type="file" onChange={handleFileSelect} hidden /></label> to upload</p>
                    <p className="file-size-info">PDF files only, maximum size 10MB</p>
                  </>
                )}
              </div>

              {Object.keys(uploadProgress).map(fileName => (
                <div className="file-item" key={fileName}>
                  <div className="file-icon">
                    {fileName.endsWith('.pdf') ? (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="#FF5252">
                        <path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v1.25c0 .41-.34.75-.75.75s-.75-.34-.75-.75V8c0-.55.45-1 1-1H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2c-.28 0-.5-.22-.5-.5v-5c0-.28.22-.5.5-.5h2c.83 0 1.5.67 1.5 1.5v3zm4-3.75c0 .41-.34.75-.75.75H19v1h.75c.41 0 .75.34.75.75s-.34.75-.75.75H19v1.25c0 .41-.34.75-.75.75s-.75-.34-.75-.75V8c0-.55.45-1 1-1h1.25c.41 0 .75.34.75.75zM9 9.5h1v-1H9v1zM3 6c-.55 0-1 .45-1 1v13c0 1.1.9 2 2 2h13c.55 0 1-.45 1-1s-.45-1-1-1H5c-.55 0-1-.45-1-1V7c0-.55-.45-1-1-1zm11 5.5h1v-3h-1v3z"/>
                      </svg>
                    ) : (
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="#4CAF50">
                        <path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/>
                      </svg>
                    )}
                  </div>
                  <div className="file-info">
                    <div className="file-name">{fileName}</div>
                    <div className="progress-bar-container">
                      <div className="progress-bar" style={{ width: `${uploadProgress[fileName]}%` }}></div>
                    </div>
                    <div className="progress-text">{uploadProgress[fileName]}% uploaded</div>
                  </div>
                  <button className="remove-btn" onClick={() => {
                    const newProgress = {...uploadProgress};
                    delete newProgress[fileName];
                    setUploadProgress(newProgress);
                    if (file && file.name === fileName) {
                      setFile(null);
                    }
                  }}>✕</button>
                </div>
              ))}
              
              <div className="action-buttons">
                <button 
                  className="cancel-btn" 
                  onClick={handleCancel}
                  disabled={isUploading}
                >
                  Cancel
                </button>
                <button 
                  className={`upload-btn ${!file || !selectedAssignment || !subject || isUploading ? 'disabled' : ''}`} 
                  onClick={handleUpload}
                  disabled={!file || !selectedAssignment || !subject || isUploading}
                >
                  {isUploading ? (
                    <span className="loading-spinner">
                      <svg className="spinner" viewBox="0 0 24 24">
                        <circle className="spinner-path" cx="12" cy="12" r="10" fill="none" strokeWidth="3"></circle>
                      </svg>
                      <span className="loading-text">Uploading...</span>
                    </span>
                  ) : (
                    'Upload'
                  )}
                </button>
              </div>
            </div>
          ) : (
            <div className="review-notification">
              <div className="review-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="#5c7cfa" strokeWidth="2"/>
                  <path d="M12 8V12L14 14" stroke="#5c7cfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3>Assignment Under Review</h3>
              {isButtonLocked ? (
                <p>
                  Your assignment has been successfully submitted and is currently being reviewed. 
                  <span className="countdown-timer">
                    Please wait <strong>{formatTime(cooldownTime)}</strong> before submitting another assignment.
                  </span> 
                  You will be notified once the review process is complete.
                </p>
              ) : (
                <p>Your assignment has been successfully submitted and is currently being reviewed. You will be notified once the review process is complete.</p>
              )}
              <button 
                className={`submit-another-btn ${isButtonLocked ? 'disabled' : ''}`} 
                onClick={() => setUploadSuccessful(false)}
                disabled={isButtonLocked}
              >
                {isButtonLocked 
                  ? `Wait ${formatTime(cooldownTime)} to Submit Again` 
                  : 'Submit Another Assignment'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}