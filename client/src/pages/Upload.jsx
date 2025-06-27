import { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import './Upload.css';
import { IoMdArrowRoundBack } from "react-icons/io";
import { BiLogOut } from "react-icons/bi";
import { BsFire } from "react-icons/bs";
import { FaLock } from "react-icons/fa";
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { connectWallet, mintNFTContract, isWalletConnected, getConnectedAccount } from '../services/walletService';
// import { connectWallet } from '../services/walletService';
import { IoWallet } from "react-icons/io5";
import { AiFillSafetyCertificate } from "react-icons/ai";




export default function Upload() {
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [isMinting, setIsMinting] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMinted, setIsMinted] = useState(false);

  useEffect(() => {
    const checkWalletConnection = async () => {
      try {
        const isConnected = await isWalletConnected();
        if (isConnected) {
          const account = await getConnectedAccount();
          setWalletConnected(true);
          setWalletAddress(account);
        }
      } catch (error) {
        console.error("Error checking wallet connection:", error);
      }
    };

    checkWalletConnection();

    // Listen for account changes
    if (typeof window.ethereum !== 'undefined') {
      window.ethereum.on('accountsChanged', (accounts) => {
        if (accounts.length === 0) {
          setWalletConnected(false);
          setWalletAddress('');
        } else {
          setWalletConnected(true);
          setWalletAddress(accounts[0]);
        }
      });

      // Listen for network changes
      window.ethereum.on('chainChanged', () => {
        window.location.reload();
      });
    }

    // Cleanup listeners
    return () => {
      if (typeof window.ethereum !== 'undefined') {
        window.ethereum.removeAllListeners('accountsChanged');
        window.ethereum.removeAllListeners('chainChanged');
      }
    };
  }, []);

  // Wallet connection function
  const handleConnectWallet = async () => {
    setIsConnecting(true);
    try {
      const address = await connectWallet();
      setWalletConnected(true);
      setWalletAddress(address);
      toast.success('Wallet connected successfully!');
    } catch (error) {
      console.error("Connection error:", error);
      toast.error(error.message);
    } finally {
      setIsConnecting(false);
    }
  };

 

  // Add notification state
  const [notificationCount, setNotificationCount] = useState(0);
  const [showNotification, setShowNotification] = useState(false);
  const [notifications, setNotifications] = useState([]);
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

   const handleMintCertificate = async () => {
    // Check if all requirements are met
    if (calculateProgress() !== 100) {
      toast.error('Complete all assignments before minting!');
      return;
    }

    if (!walletConnected) {
      toast.error('Please connect your wallet first!');
      return;
    }

    setIsMinting(true);

    try {
      const defaultSubjects = [
      'Blockchain Development',
      'Smart Contract Programming',
      'Cryptocurrency Trading',
      'DeFi Protocols',
      'NFT Creation',
      'Web3 Development',
      'Ethereum Development',
      'Solidity Programming',
      'Decentralized Applications',
      'Crypto Security'
    ];

    const issuers = [
      'Udemy',
      'Coursera',
      'edX',
      'Khan Academy',
      'MIT OpenCourseWare',
      'Stanford Online',
      'Harvard Extension',
      'Berkeley Online',
      'Yale Open Courses',
      'Princeton Online',
      'Columbia Digital',
      'NYU Online'
    ];
    const signatures = [
      'Dr. Sarah Johnson',
      'Prof. Michael Chen',
      'Dr. Emily Davis',
      'Prof. David Wilson',
      'Dr. Lisa Anderson',
      'Prof. Robert Martinez',
      'Dr. Jennifer Lee',
      'Prof. Christopher Brown',
      'Dr. Amanda Taylor',
      'Prof. Kevin Singh',
      'Dr. Rachel Thompson'
    ];

    const randomCourses = [
      'Complete Web Development Bootcamp',
      'Advanced JavaScript Masterclass',
      'Full Stack Development Course',
      'React & Node.js Certification',
      'Python Programming Fundamentals',
      'Data Science & Machine Learning',
      'Cybersecurity Essentials',
      'Digital Marketing Strategy',
      'UI/UX Design Principles',
      'Cloud Computing with AWS',
      'Mobile App Development',
      'Database Design & Management',
      'DevOps Engineering Track',
      'Artificial Intelligence Course',
      'Game Development with Unity',
      'E-commerce Development',
      'Network Security Fundamentals',
      'Business Analytics Course',
      'Project Management Certification',
      'Software Testing & QA'
    ];
        const getRandomItem = (array) => array[Math.floor(Math.random() * array.length)];

      // Hardcoded certificate data
    const subjectName = subject.trim() || getRandomItem(defaultSubjects);
    const issuedBy = getRandomItem(issuers);
    const signature = getRandomItem(signatures);

      const certificateSVG = `<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <!-- Background -->
  <rect width="800" height="600" fill="#fdfaf6" stroke="#333" stroke-width="8"/>

  <!-- Inner Border -->
  <rect x="20" y="20" width="760" height="560" fill="none" stroke="#999" stroke-width="2"/>

  <!-- Title -->
  <text x="400" y="100" font-size="36" text-anchor="middle"
        font-family="Georgia, serif" fill="#222">
    Certificate of Completion
  </text>

  <!-- Subtitle -->
  <text x="400" y="150" font-size="20" text-anchor="middle"
        font-family="Arial, sans-serif" fill="#666">
    This certifies that
  </text>

  <!-- Student Name -->
  <text x="400" y="210" font-size="30" text-anchor="middle"
        font-family="Georgia, serif" fill="#000" font-weight="bold">
    ${user?.name || 'Student'}
  </text>

  <!-- Course Statement -->
  <text x="400" y="270" font-size="18" text-anchor="middle"
        font-family="Arial, sans-serif" fill="#444">
    has successfully completed the course
  </text>

  <!-- Course Name -->
  <text x="400" y="310" font-size="24" text-anchor="middle"
        font-family="Georgia, serif" fill="#000">
    ${subjectName.trim()}
  </text>

  <!-- Provider Name -->
  <text x="400" y="370" font-size="18" text-anchor="middle"
        font-family="Arial, sans-serif" fill="#444">
    Issued by ${issuedBy}
  </text>

  <!-- Date Field -->
  <text x="120" y="500" font-size="16" font-family="Arial, sans-serif" fill="#333">
    Date: ${new Date().toLocaleDateString() || 'MM/DD/YYYY'}
  </text>

  <text x="670" y="470" font-size="14" text-anchor="middle"
        font-family="Arial, sans-serif" fill="#333">
    ${signature}
  </text>
  <!-- Signature Line -->
  <line x1="600" y1="480" x2="740" y2="480" stroke="#333" stroke-width="1"/>
  <text x="670" y="500" font-size="14" text-anchor="middle"
        font-family="Arial, sans-serif" fill="#333">
    Signature
  </text>
</svg>`; // Hardcoded base64 image (~2700 chars)
      const base64Image = `data:image/svg+xml;base64,${btoa(certificateSVG)}`;      
      const course = getRandomItem(randomCourses); // ~200 chars

      
      const result = await mintNFTContract(base64Image, subjectName, course);

      if (result.success) {
        setIsMinted(true);
        toast.success(`🎉 Certificate minted successfully! Transaction: ${result.transactionHash.slice(0, 10)}...`);
        console.log('Certificate minted:', result);
      }
    } catch (error) {
      
      console.error('Minting failed:', error);
    } finally {
      setIsMinting(false);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem('notifications');
    if (saved) {
      setNotifications(JSON.parse(saved));
      setNotificationCount(JSON.parse(saved).length);
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('uploadSuccessful', JSON.stringify(uploadSuccessful));
  }, [uploadSuccessful]);
  
   // Poll every 5 seconds
  useEffect(() => {
    if (!user?.id) return;

    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`http://localhost:3900/reviewed-assignments/${user.id}`);
        const reviewed = res.data;

        if (reviewed.length > 0) {
          setAssignments(prev => {
            // Create a new array with updated assignments
            const updatedAssignments = prev.map(assignment => {
              const match = reviewed.find(r => r.assignmentId == assignment.id);
              if (match && assignment.status !== 'Submitted') {
                // Show toast only if status changed
                toast.success(`✅ Assignment ${assignment.id} has been reviewed!`);
                return { ...assignment, status: 'Submitted' };
              }
              return assignment;
            });
            
            // Save the updated assignments to localStorage
            localStorage.setItem('assignments', JSON.stringify(updatedAssignments));
            
            // Return the updated assignments for state update
            return updatedAssignments;
          });

          // Optionally clear the reviewed data from backend
          // axios.delete(`http://localhost:3900/reviewed-assignments/${user.id}`);
        }
      } catch (err) {
        console.error("Error fetching reviewed assignments:", err);
      }
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, [user]);

  useEffect(() => {
  if (!user?.id) return;

  const fetchNotifications = async () => {
    try {
      const res = await axios.get(`http://localhost:3900/notifications/${user.id}`);
      const newNotifications = res.data;

      if (newNotifications.length > 0) {
        // Use functional updates to avoid creating a dependency on notifications
        setNotifications(prevNotifications => {
          // Filter out already seen ones
          const unseen = newNotifications.filter(n =>
            !prevNotifications.some(existing => existing.assignmentId === n.assignmentId)
          );

          if (unseen.length > 0) {
            const updatedNotifications = [...unseen, ...prevNotifications];
            localStorage.setItem('notifications', JSON.stringify(updatedNotifications));
            
            // Update notification count
            setNotificationCount(unseen.length);
            
            return updatedNotifications;
          }
          
          return prevNotifications;
        });
      }
    } catch (err) {
      console.error("Error fetching notifications:", err);
    }
  };

  fetchNotifications(); // Initial fetch
  const interval = setInterval(fetchNotifications, 5000);

  return () => clearInterval(interval);
}, [user]); // Remove notifications from dependencies

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

      // Show toast using server message if available
    if (res.data && res.data.success) {
      toast.success(res.data.message || 'Assignment uploaded successfully!');
    } else {
      toast.success('Assignment uploaded successfully!');
    }
      
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
      
      // toast.success('Assignment uploaded successfully!');
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

  // Function to handle notification click
  const handleNotificationClick = () => {
  setShowNotification(!showNotification);
  setNotificationCount(0);

  // Optional: Clear local storage count only when viewed
  const updatedNotifications = notifications.map(n => ({ ...n, read: true }));
  localStorage.setItem('notifications', JSON.stringify(updatedNotifications));
};

  useEffect(() => {
  console.log('Current assignments:', assignments);
  console.log('Progress calculation:', calculateProgress());
  
  // Check what's in localStorage
  const savedAssignments = localStorage.getItem('assignments');
  if (savedAssignments) {
    console.log('Assignments in localStorage:', JSON.parse(savedAssignments));
  } else {
    console.log('No assignments found in localStorage');
  }
}, [assignments]);

  // Add this function inside your component
  const calculateProgress = () => {
  try {
    // First check if we can get data from localStorage directly
    const savedAssignments = localStorage.getItem('assignments');
    let assignmentsToUse = assignments;
    
    if (savedAssignments) {
      // Use the most recent data from localStorage if available
      const parsedAssignments = JSON.parse(savedAssignments);
      if (Array.isArray(parsedAssignments) && parsedAssignments.length > 0) {
        assignmentsToUse = parsedAssignments;
      }
    }
    
    const totalAssignments = assignmentsToUse.length;
    const submittedAssignments = assignmentsToUse.filter(
      assignment => assignment.status === 'Submitted'
    ).length;
    
    // Calculate percentage and round to nearest whole number
    return totalAssignments > 0 
      ? Math.round((submittedAssignments / totalAssignments) * 100) 
      : 0;
  } catch (error) {
    console.error("Error calculating progress:", error);
    return 0;
  }
};

  

  // Rest of your component remains the same
  return (
    <div className="dashboard-container">
      <ToastContainer theme="dark" position="top-right" />
      
      <div className="header">
        <div className="user-section">
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
          
          <div className="navigation-path">
            <Link to="/" className="path-link">Home</Link>
            <span className="path-separator">/</span>
            <Link to="/nfts" className="path-link">NFT Certificates</Link>
            <span className="path-separator">/</span>
            <Link to="/dashboard" className="path-link">Dashboard</Link>
            <span className="path-separator">/</span>
            <Link className='assignment-progress'>Progress <span className='style-progress-value'>{calculateProgress()}%</span></Link>
          </div>
          
        </div>
        
        <div className="header-right">
          {/* Notification Bell */}
          <div className="notification-container">
            <button className="notification-btn" onClick={handleNotificationClick}>
              <BsFire style={{verticalAlign:'middle'}} size={22}/>
              <span className="notification-badge">{notificationCount}</span>
            </button>

            {showNotification && (
              <div className="notification-dropdown">
                {notifications.length > 0 ? (
                  <div className="notification-list">
                    {notifications.map((notif, index) => (
                      <div key={index} className="notification-item">
                        <strong>Assignment {notif.assignmentId}</strong><br />
                        {notif.feedback || "Your assignment has been reviewed."}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="notification-empty">No notifications yet.</div>
                )}
              </div>
            )}
          </div>
          
          <button className="back-btn" onClick={() => navigate(-1)}>
            <IoMdArrowRoundBack style={{verticalAlign:'middle'}} size={20}/> Back
          </button>
          <button className="logout-btn" onClick={handleLogout}>
            <BiLogOut style={{verticalAlign:'middle',marginRight:'7px'}} size={20} />
            Logout
          </button>
        </div>
      </div>
      
      <div className="dashboard-content">
        {/* Left panel remains the same */}
        <div className="left-panel">
          <div className="assignment-header">
    <div className="assignment-counter">
      Total Assignments - {assignments.length}
    </div>
    
    {/* Single button that changes based on wallet connection status */}
  {!walletConnected ? (
    <button 
      onClick={handleConnectWallet}
      disabled={isConnecting}
      className="connect-wallet-btn"
    >
      {isConnecting ? (
  'Connecting...'
) : (
  <>
    <IoWallet style={{ marginRight: '8px',verticalAlign:'middle' }} />
    Connect Wallet
  </>
)}
    </button>
  ) : (
    <button 
      onClick={handleMintCertificate}
      disabled={calculateProgress() < 100 || isMinting}
      className={`mint-btn ${calculateProgress() < 100 ? 'locked' : 'unlocked'}`}
    >
      {calculateProgress() < 100 ? (
        <>
          <span className="lock-icon"><FaLock size={15}  style={{verticalAlign:'middle', marginRight:'8px', color:'#2CBB5D'}}/></span>
          Mint ({calculateProgress()}%)
        </>
      ) : isMinting ? (
        <>
          <span className="loading-icon">⏳</span>
          Minting...
        </>
      ) : (
        <>
          <span className="unlock-icon"><AiFillSafetyCertificate size={17} style={{verticalAlign:'middle',marginRight:'8px' , color:'#2CBB5D'}}/></span>
          Mint Certificate
        </>
      )}
    </button>
  )}
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