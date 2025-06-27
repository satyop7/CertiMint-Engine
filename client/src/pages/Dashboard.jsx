import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  FaArrowLeft, 
  FaUser, 
  FaFileAlt, 
  FaExclamationTriangle, 
  FaCheckCircle, 
  FaTimesCircle,
  FaRobot,
  FaCopy,
  FaEye,
  FaCalendarAlt,
  FaChartPie,
  FaChartBar,
  FaKeyboard,
  FaExclamationCircle
} from 'react-icons/fa';
import { 
  MdOutlineSubject, 
  MdOutlinePercent, 
  MdOutlineSmartToy,
  MdOutlineWarning,
  MdOutlineAnalytics 
} from 'react-icons/md';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LineChart,
  Line,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import './Dashboard.scss';

const Dashboard = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [assignments, setAssignments] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 8,
    hasNextPage: false,
    hasPrevPage: false
  });
  const [stats, setStats] = useState({
    total: 0,
    passed: 0,
    failed: 0,
    pending: 0,
    aiDetected: 0,
    plagiarismDetected: 0
  });
  const [subjectChartData, setSubjectChartData] = useState([]);
  const [monthlyChartData, setMonthlyChartData] = useState([]);

  const assignmentsPerPage = 8;
  const API_BASE_URL = 'http://localhost:3900/api';

  // Safe data access helper functions
  const safeGet = (obj, path, defaultValue = null) => {
    try {
      return path.split('.').reduce((current, key) => {
        return current && typeof current === 'object' ? current[key] : defaultValue;
      }, obj) ?? defaultValue;
    } catch {
      return defaultValue;
    }
  };

  const safeNumber = (value, defaultValue = 0) => {
    return typeof value === 'number' && !isNaN(value) ? value : defaultValue;
  };

  const safeString = (value, defaultValue = 'N/A') => {
    return typeof value === 'string' && value.trim() ? value : defaultValue;
  };

  const safeBoolean = (value, defaultValue = false) => {
    return typeof value === 'boolean' ? value : defaultValue;
  };

  const safeArray = (value, defaultValue = []) => {
    return Array.isArray(value) ? value : defaultValue;
  };

  useEffect(() => {
    if (user?.name) {
      fetchAssignments();
      fetchStats();
    }
  }, [currentPage, user?.name]);

  const fetchAssignments = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(
        `${API_BASE_URL}/assignments/user/${encodeURIComponent(user.name)}?page=${currentPage}&limit=${assignmentsPerPage}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Process assignments with correct MongoDB schema
        const processedAssignments = (data.data || []).map(assignment => ({
          ...assignment,
          _id: assignment._id || `temp_${Date.now()}_${Math.random()}`,
          subject: safeString(assignment.subject, 'Unknown'),
          assignment_id: safeString(assignment.assignment_id, 'N/A'),
          status: safeString(assignment.status, 'PENDING'),
          ocr_text_length: safeNumber(assignment.ocr_text_length, 0),
          ocr_text_preview: safeString(assignment.ocr_text_preview, 'No preview available'),
          upload_timestamp: assignment.upload_timestamp || new Date().toISOString(),
          username: safeString(assignment.username, 'Unknown'),
          
          // Correct plagiarism_check structure
          plagiarism_check: {
            plagiarism_detected: safeBoolean(safeGet(assignment, 'plagiarism_check.plagiarism_detected'), false),
            plagiarism_percentage: safeNumber(safeGet(assignment, 'plagiarism_check.plagiarism_percentage'), 0),
            ai_patterns_detected: safeBoolean(safeGet(assignment, 'plagiarism_check.ai_patterns_detected'), false),
            ai_confidence: safeNumber(safeGet(assignment, 'plagiarism_check.ai_confidence'), 0),
            semantic_similarity: safeNumber(safeGet(assignment, 'plagiarism_check.semantic_similarity'), 0),
            statistical_similarity: safeNumber(safeGet(assignment, 'plagiarism_check.statistical_similarity'), 0),
            ngram_similarity: safeNumber(safeGet(assignment, 'plagiarism_check.ngram_similarity'), 0),
            
            // AI patterns and feature scores
            ai_patterns: safeGet(assignment, 'plagiarism_check.ai_patterns', {}),
            feature_scores: {
              paragraph_consistency: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.paragraph_consistency'), 0),
              sentence_variety: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.sentence_variety'), 0),
              lexical_diversity: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.lexical_diversity'), 0),
              repetitive_patterns: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.repetitive_patterns'), 0),
              structural_patterns: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.structural_patterns'), 0),
              top_features_score: safeNumber(safeGet(assignment, 'plagiarism_check.feature_scores.top_features_score'), 0)
            }
          },
          
          // Content validation
          content_validation: {
            status: safeString(safeGet(assignment, 'content_validation.status'), 'PENDING'),
            relevance_score: safeNumber(safeGet(assignment, 'content_validation.relevance_score'), 0),
            groq_word_score: safeNumber(safeGet(assignment, 'content_validation.groq_word_score'), 0),
            phi_llm_score: safeNumber(safeGet(assignment, 'content_validation.phi_llm_score'), 0)
          },
          
          // Arrays
          failure_reasons: safeArray(assignment.failure_reasons, []),
          groq_words_used: safeArray(safeGet(assignment, 'groq_words_used'), [])
        }));

        setAssignments(processedAssignments);
        setPagination(data.pagination || {
          currentPage: 1,
          totalPages: 1,
          totalItems: 0,
          itemsPerPage: assignmentsPerPage,
          hasNextPage: false,
          hasPrevPage: false
        });
      } else {
        throw new Error(data.error || 'Failed to fetch assignments');
      }
    } catch (error) {
      console.error('Error fetching assignments:', error);
      setError(error.message);
      setAssignments([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/assignments/stats/user/${encodeURIComponent(user.name)}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setStats({
          total: safeNumber(safeGet(data, 'stats.total'), 0),
          passed: safeNumber(safeGet(data, 'stats.passed'), 0),
          failed: safeNumber(safeGet(data, 'stats.failed'), 0),
          pending: safeNumber(safeGet(data, 'stats.pending'), 0),
          aiDetected: safeNumber(safeGet(data, 'stats.aiDetected'), 0),
          plagiarismDetected: safeNumber(safeGet(data, 'stats.plagiarismDetected'), 0)
        });
        
        // Process subject distribution data
        const subjectData = (data.subjectDistribution || []).map(item => ({
          subject: safeString(item.subject, 'Unknown'),
          count: safeNumber(item.count, 0)
        }));
        setSubjectChartData(subjectData);
        
        // Generate monthly data from assignments (if not provided by backend)
        generateMonthlyData();
      } else {
        console.error('Failed to fetch stats:', data.error);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const generateMonthlyData = () => {
    // Generate monthly data from current assignments
    const monthlyData = assignments.reduce((acc, assignment) => {
      try {
        const date = new Date(assignment.upload_timestamp);
        const month = date.toLocaleDateString('en-US', { month: 'short' });
        acc[month] = (acc[month] || 0) + 1;
      } catch {
        // Skip invalid dates
      }
      return acc;
    }, {});

    const monthlyChartData = Object.entries(monthlyData).map(([month, count]) => ({
      month,
      submissions: count
    }));
    
    setMonthlyChartData(monthlyChartData);
  };

  // Generate feature scores radar chart data
  const getFeatureScoreData = (assignment) => {
    const features = assignment.plagiarism_check?.feature_scores || {};
    return [
      { feature: 'Paragraph Consistency', value: features.paragraph_consistency || 0 },
      { feature: 'Sentence Variety', value: features.sentence_variety || 0 },
      { feature: 'Lexical Diversity', value: features.lexical_diversity || 0 },
      { feature: 'Structural Patterns', value: features.structural_patterns || 0 },
      { feature: 'Top Features', value: features.top_features_score || 0 }
    ];
  };

  // Chart data with null handling
  const statusData = [
    { name: 'Passed', value: stats.passed, color: '#10B981' },
    { name: 'Failed', value: stats.failed, color: '#EF4444' },
    { name: 'Pending', value: stats.pending, color: '#F59E0B' }
  ].filter(item => item.value > 0); // Only show non-zero values

  const getStatusColor = (status) => {
    switch (status?.toUpperCase()) {
      case 'PASSED': return '#10B981';
      case 'FAILED': return '#EF4444';
      case 'PENDING': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status?.toUpperCase()) {
      case 'PASSED': return <FaCheckCircle className="status-icon passed" />;
      case 'FAILED': return <FaTimesCircle className="status-icon failed" />;
      case 'PENDING': return <FaExclamationTriangle className="status-icon pending" />;
      default: return <FaFileAlt className="status-icon" />;
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Invalid Date';
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.totalPages) {
      setCurrentPage(newPage);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <div className="error-content">
          <h2>Error Loading Dashboard</h2>
          <p>{error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <button className="back-button" onClick={() => navigate('/upload')}>
          <FaArrowLeft /> Back
        </button>
        
        <div className="user-info">
          <img 
            src={user?.picture || '/default-avatar.png'} 
            alt={user?.name || 'User'} 
            className="user-avatar"
          />
          <div className="user-details">
            <h2>Welcome back, {user?.name || 'User'}!</h2>
            <p>{user?.email || 'No email provided'}</p>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-icon">
            <FaFileAlt />
          </div>
          <div className="stat-content">
            <h3>{stats.total}</h3>
            <p>Total Assignments</p>
          </div>
        </div>

        <div className="stat-card passed">
          <div className="stat-icon">
            <FaCheckCircle />
          </div>
          <div className="stat-content">
            <h3>{stats.passed}</h3>
            <p>Passed</p>
          </div>
        </div>

        <div className="stat-card failed">
          <div className="stat-icon">
            <FaTimesCircle />
          </div>
          <div className="stat-content">
            <h3>{stats.failed}</h3>
            <p>Failed</p>
          </div>
        </div>

        <div className="stat-card ai-detected">
          <div className="stat-icon">
            <FaRobot />
          </div>
          <div className="stat-content">
            <h3>{stats.aiDetected}</h3>
            <p>AI Detected</p>
          </div>
        </div>

        <div className="stat-card plagiarism">
          <div className="stat-icon">
            <FaCopy />
          </div>
          <div className="stat-content">
            <h3>{stats.plagiarismDetected}</h3>
            <p>Plagiarism Found</p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        {statusData.length > 0 && (
          <div className="chart-card">
            <h3><FaChartPie /> Assignment Status Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="value"
                  label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {subjectChartData.length > 0 && (
          <div className="chart-card subjects-chart">
            <h3><FaChartBar /> Subjects Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={subjectChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis 
                  dataKey="subject" 
                  tick={{ fill: '#f0f0f0', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                  tickLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                />
                <YAxis 
                  tick={{ fill: '#f0f0f0', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                  tickLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(26, 26, 26, 0.95)',
                    border: '1px solid rgba(251, 233, 217, 0.3)',
                    borderRadius: '8px',
                    color: '#f0f0f0',
                    fontSize: '14px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                    backdropFilter: 'blur(10px)'
                  }}
                  labelStyle={{
                    color: '#FBE9D9',
                    fontWeight: '600',
                    marginBottom: '4px'
                  }}
                  itemStyle={{
                    color: '#f0f0f0'
                  }}
                  cursor={false}
                />
                <Bar 
                  dataKey="count" 
                  fill="#FBE9D9"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {monthlyChartData.length > 0 && (
          <div className="chart-card full-width">
            <h3><FaCalendarAlt /> Monthly Submissions</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={monthlyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
                <XAxis 
                  dataKey="month"
                  tick={{ fill: '#f0f0f0', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                  tickLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                />
                <YAxis 
                  tick={{ fill: '#f0f0f0', fontSize: 12 }}
                  axisLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                  tickLine={{ stroke: 'rgba(255, 255, 255, 0.2)' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'rgba(26, 26, 26, 0.95)',
                    border: '1px solid rgba(251, 233, 217, 0.3)',
                    borderRadius: '8px',
                    color: '#f0f0f0',
                    fontSize: '14px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)',
                    backdropFilter: 'blur(10px)'
                  }}
                  labelStyle={{
                    color: '#FBE9D9',
                    fontWeight: '600',
                    marginBottom: '4px'
                  }}
                  itemStyle={{
                    color: '#f0f0f0'
                  }}
                  cursor={false}
                />
                <Legend />
                <Line type="monotone" dataKey="submissions" stroke="#FBE9D9" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Assignments Table */}
      <div className="assignments-section">
        <h3>Recent Assignments</h3>
        
        {assignments.length === 0 ? (
          <div className="no-assignments">
            <FaFileAlt size={48} />
            <h4>No assignments found</h4>
            <p>Upload your first assignment to get started!</p>
            <button onClick={() => navigate('/upload')} className="btn-primary">
              Upload Assignment
            </button>
          </div>
        ) : (
          <>
            <div className="assignments-grid">
              {assignments.map((assignment, index) => (
                <div 
                  key={assignment._id || `assignment-${index}`}
                  className={`assignment-card ${assignment.status?.toLowerCase() || 'pending'}`}
                  onClick={() => setSelectedAssignment(assignment)}
                >
                  <div className="assignment-header">
                    <div className="assignment-id">
                      <FaFileAlt />
                      <span>Assignment-{assignment.assignment_id}</span>
                    </div>
                    {getStatusIcon(assignment.status)}
                  </div>

                  <div className="assignment-content">
                    <div className="assignment-subject">
                      <MdOutlineSubject />
                      <span>{assignment.subject}</span>
                    </div>

                    <div className="assignment-stats">
                      <div className="stat">
                        <MdOutlinePercent />
                        <span>Plagiarism: {assignment.plagiarism_check?.plagiarism_percentage?.toFixed(1) || '0.0'}%</span>
                      </div>
                      
                      <div className="stat">
                        <MdOutlineSmartToy />
                        <span>AI: {assignment.plagiarism_check?.ai_confidence?.toFixed(1) || '0.0'}%</span>
                      </div>
                    </div>

                    <div className="assignment-meta">
                      <span className="date">
                        <FaCalendarAlt />
                        {formatDate(assignment.upload_timestamp)}
                      </span>
                      <span className="length">
                        {assignment.ocr_text_length} chars
                      </span>
                    </div>

                    {assignment.failure_reasons && assignment.failure_reasons.length > 0 && (
                      <div className="failure-reason">
                        <MdOutlineWarning />
                        <span>{assignment.failure_reasons[0].substring(0, 80)}...</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            <div className="pagination">
              <button 
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={!pagination.hasPrevPage}
                className="pagination-btn"
              >
                Previous
              </button>
              
              <div className="pagination-info">
                <span>Page {pagination.currentPage} of {pagination.totalPages}</span>
                <span>({pagination.totalItems} total assignments)</span>
              </div>
              
              <button 
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={!pagination.hasNextPage}
                className="pagination-btn"
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>

      {/* Assignment Detail Modal */}
      {selectedAssignment && (
        <div className="modal-overlay" onClick={() => setSelectedAssignment(null)}>
          <div className="assignment-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedAssignment.assignment_id}</h3>
              <button onClick={() => setSelectedAssignment(null)}>&times;</button>
            </div>
            
            <div className="modal-content">
              <div className="modal-section">
                <h4>Basic Information</h4>
                <div className="info-grid">
                  <div><strong>Subject:</strong> {selectedAssignment.subject}</div>
                  <div><strong>Status:</strong> 
                    <span className={`status ${selectedAssignment.status?.toLowerCase() || 'pending'}`}>
                      {selectedAssignment.status || 'PENDING'}
                    </span>
                  </div>
                  <div><strong>Upload Date:</strong> {formatDate(selectedAssignment.upload_timestamp)}</div>
                  <div><strong>Text Length:</strong> {selectedAssignment.ocr_text_length} characters</div>
                </div>
              </div>

              <div className="modal-section">
                <h4>Plagiarism Analysis</h4>
                <div className="analysis-grid">
                  <div><strong>Plagiarism Detected:</strong> 
                    <span className={selectedAssignment.plagiarism_check?.plagiarism_detected ? 'danger' : 'success'}>
                      {selectedAssignment.plagiarism_check?.plagiarism_detected ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div><strong>Plagiarism %:</strong> {selectedAssignment.plagiarism_check?.plagiarism_percentage?.toFixed(2) || '0.00'}%</div>
                  <div><strong>Statistical Similarity:</strong> {selectedAssignment.plagiarism_check?.statistical_similarity?.toFixed(2) || '0.00'}%</div>
                  <div><strong>Semantic Similarity:</strong> {selectedAssignment.plagiarism_check?.semantic_similarity?.toFixed(2) || '0.00'}%</div>
                  <div><strong>N-gram Similarity:</strong> {selectedAssignment.plagiarism_check?.ngram_similarity?.toFixed(2) || '0.00'}%</div>
                </div>
              </div>

              <div className="modal-section">
                <h4>AI Detection</h4>
                <div className="analysis-grid">
                  <div><strong>AI Patterns:</strong> 
                    <span className={selectedAssignment.plagiarism_check?.ai_patterns_detected ? 'danger' : 'success'}>
                      {selectedAssignment.plagiarism_check?.ai_patterns_detected ? 'Detected' : 'Not Detected'}
                    </span>
                  </div>
                  <div><strong>AI Confidence:</strong> {selectedAssignment.plagiarism_check?.ai_confidence?.toFixed(2) || '0.00'}%</div>
                </div>
              </div>

              {/* Feature Scores Radar Chart */}
              {selectedAssignment.plagiarism_check?.feature_scores && (
                <div className="modal-section">
                  <h4><MdOutlineAnalytics /> Feature Analysis</h4>
                  <div className="feature-chart-container">
                    <ResponsiveContainer width="100%" height={250}>
                      <RadarChart data={getFeatureScoreData(selectedAssignment)}>
                        <PolarGrid stroke="rgba(255, 255, 255, 0.2)" />
                        <PolarAngleAxis 
                          dataKey="feature" 
                          tick={{ fill: '#f0f0f0', fontSize: 10 }}
                        />
                        <PolarRadiusAxis 
                          tick={{ fill: '#f0f0f0', fontSize: 8 }}
                          domain={[0, 100]}
                        />
                        <Radar
                          name="Score"
                          dataKey="value"
                          stroke="#FBE9D9"
                          fill="rgba(251, 233, 217, 0.3)"
                          strokeWidth={2}
                        />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: 'rgba(26, 26, 26, 0.95)',
                            border: '1px solid rgba(251, 233, 217, 0.3)',
                            borderRadius: '8px',
                            color: '#f0f0f0'
                          }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="feature-details">
                    <div className="feature-item">
                      <strong>Repetitive Patterns:</strong> {selectedAssignment.plagiarism_check?.feature_scores?.repetitive_patterns?.toFixed(2) || '0.00'}
                    </div>
                  </div>
                </div>
              )}

              <div className="modal-section">
                <h4>Content Validation</h4>
                <div className="analysis-grid">
                  <div><strong>Validation Status:</strong> 
                    <span className={`status ${selectedAssignment.content_validation?.status?.toLowerCase() || 'pending'}`}>
                      {selectedAssignment.content_validation?.status || 'PENDING'}
                    </span>
                  </div>
                  <div><strong>Relevance Score:</strong> {selectedAssignment.content_validation?.relevance_score || 0}/100</div>
                  <div><strong>Phi LLM Score:</strong> {selectedAssignment.content_validation?.phi_llm_score || 0}/100</div>
                </div>
              </div>

              {/* Groq Words Used */}
              {selectedAssignment.groq_words_used && selectedAssignment.groq_words_used.length > 0 && (
                <div className="modal-section">
                  <h4><FaKeyboard /> Keywords Used</h4>
                  <div className="keywords-container">
                    {selectedAssignment.groq_words_used.map((word, index) => (
                      <span key={index} className="keyword-tag">
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* All Failure Reasons */}
              {selectedAssignment.failure_reasons && selectedAssignment.failure_reasons.length > 0 && (
                <div className="modal-section">
                  <h4><FaExclamationCircle /> Failure Reasons</h4>
                  <div className="failure-reasons-list">
                    {selectedAssignment.failure_reasons.map((reason, index) => (
                      <div key={index} className="failure-reason-item">
                        <FaExclamationTriangle className="failure-icon" />
                        <span>{reason}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="modal-section">
                <h4>Content Preview</h4>
                <div className="content-preview">
                  {selectedAssignment.ocr_text_preview || 'No preview available'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;