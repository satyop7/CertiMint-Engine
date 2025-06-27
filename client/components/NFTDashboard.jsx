import React, { useEffect, useState } from "react";
import { getConnectedAccount } from "../src/services/walletService";
import { contractAddress, abi } from "../src/utils/constants";
import { createPublicClient, custom } from "viem";
import { zksyncSepoliaTestnet } from "viem/chains";
import { 
  FaSearch, 
  FaWallet, 
  FaCertificate, 
  FaEye, 
  FaShare,
  FaTimes,
  FaCalendar,
  FaUser,
  FaGraduationCap,
  FaAward,
  FaFilter,
  FaTh,
  FaList,
  FaCopy,
  FaExternalLinkAlt
} from 'react-icons/fa';
import { MdVerified, MdSchool } from 'react-icons/md';
import { toast } from 'react-toastify';
import '../src/pages/NFDashboard.css'

const NFTDashboard = () => {
  const [nfts, setNfts] = useState([]);
  const [filteredNfts, setFilteredNfts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchAddress, setSearchAddress] = useState("");
  const [selectedNft, setSelectedNft] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [filterSubject, setFilterSubject] = useState('all');
  const [connectedWallet, setConnectedWallet] = useState(null);
  const [stats, setStats] = useState({
    totalCertificates: 0,
    subjects: [],
    latestCertificate: null
  });

  // Get connected account
  const getConnectedAccount = async () => {
    if (typeof window.ethereum !== "undefined") {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_accounts' });
        return accounts[0];
      } catch (err) {
        console.error("Failed to get connected account:", err);
        return null;
      }
    }
    return null;
  };

  const loadNFTsForAddress = async (address) => {
    if (!address || address.trim() === "") {
      setError("Please enter a valid wallet address.");
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const publicClient = createPublicClient({
        chain: zksyncSepoliaTestnet,
        transport: custom(window.ethereum),
      });

      const balance = await publicClient.readContract({
        address: contractAddress,
        abi: abi,
        functionName: "balanceOf",
        args: [address],
      });

      const nftList = [];

      for (let i = 0; i < Number(balance); i++) {
        const tokenId = await publicClient.readContract({
          address: contractAddress,
          abi: abi,
          functionName: "tokenOfOwnerByIndex",
          args: [address, BigInt(i)],
        });

        const uri = await publicClient.readContract({
          address: contractAddress,
          abi: abi,
          functionName: "tokenURI",
          args: [tokenId],
        });

        const dataIndex = uri.indexOf(",");
        if (dataIndex === -1) {
          console.warn(`Invalid tokenURI format for token ${tokenId}`);
          continue;
        }

        const jsonStr = uri.slice(dataIndex + 1);
        let metadata;

        try {
          metadata = JSON.parse(jsonStr);
        } catch (e) {
          console.error(`Failed to parse metadata for token ${tokenId}:`, jsonStr);
          continue;
        }

        nftList.push({
          tokenId: Number(tokenId),
          metadata,
          mintDate: new Date().toISOString(),
        });
      }

      setNfts(nftList);
      setFilteredNfts(nftList);
      updateStats(nftList);
    } catch (err) {
      console.error("Error loading NFTs:", err);
      setError(err.message || "Failed to load NFTs for this address");
    } finally {
      setLoading(false);
    }
  };

  const updateStats = (nftList) => {
    const subjects = [...new Set(nftList.map(nft => nft.metadata.Subject))];
    const latest = nftList.length > 0 ? nftList[nftList.length - 1] : null;
    
    setStats({
      totalCertificates: nftList.length,
      subjects,
      latestCertificate: latest
    });
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchAddress.trim()) {
      toast.error('Please enter a wallet address');
      return;
    }
    await loadNFTsForAddress(searchAddress);
  };

  const handleFilter = (subject) => {
    setFilterSubject(subject);
    if (subject === 'all') {
      setFilteredNfts(nfts);
    } else {
      setFilteredNfts(nfts.filter(nft => nft.metadata.Subject === subject));
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const shareCertificate = (nft) => {
    const shareData = {
      title: `Certificate: ${nft.metadata.Subject}`,
      text: `Check out my certificate for ${nft.metadata.Subject}!`,
      url: window.location.href
    };
    
    if (navigator.share) {
      navigator.share(shareData);
    } else {
      copyToClipboard(window.location.href);
    }
  };

  // Load NFTs of connected wallet initially
  useEffect(() => {
    const init = async () => {
      const connectedAddress = await getConnectedAccount();
      if (connectedAddress) {
        setConnectedWallet(connectedAddress);
        setSearchAddress(connectedAddress);
        await loadNFTsForAddress(connectedAddress);
      }
    };
    init();
  }, []);

  const formatAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="nft-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-content">
          <div className="title-section">
            <h1><FaCertificate /> Certificate Dashboard</h1>
            <p>View and manage your blockchain certificates</p>
          </div>
          
          {connectedWallet && (
            <div className="wallet-info">
              <div className="wallet-badge">
                <FaWallet />
                <span>{formatAddress(connectedWallet)}</span>
                <button onClick={() => copyToClipboard(connectedWallet)}>
                  <FaCopy />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Search Section */}
      <div className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-group">
            <FaSearch className="search-icon" />
            <input
              type="text"
              placeholder="Enter wallet address to view certificates..."
              value={searchAddress}
              onChange={(e) => setSearchAddress(e.target.value)}
              className="search-input"
            />
            <button type="submit" className="search-button">
              <span>Search</span>
            </button>
          </div>
        </form>

        {connectedWallet && (
          <button 
            className="my-wallet-btn"
            onClick={() => {
              setSearchAddress(connectedWallet);
              loadNFTsForAddress(connectedWallet);
            }}
          >
            <FaWallet /> My Certificates
          </button>
        )}
      </div>

      {/* Stats Section */}
      {!loading && !error && nfts.length > 0 && (
        <div className="stats-section">
          <div className="stat-card">
            <div className="stat-icon">
              <FaAward />
            </div>
            <div className="stat-content">
              <h3>{stats.totalCertificates}</h3>
              <p>Total Certificates</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <MdSchool />
            </div>
            <div className="stat-content">
              <h3>{stats.subjects.length}</h3>
              <p>Unique Subjects</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <MdVerified />
            </div>
            <div className="stat-content">
              <h3>Verified</h3>
              <p>Blockchain Secured</p>
            </div>
          </div>
        </div>
      )}

      {/* Controls */}
      {!loading && !error && nfts.length > 0 && (
        <div className="controls-section">
          <div className="filter-controls">
            <div className="filter-group">
              <FaFilter />
              <select 
                value={filterSubject} 
                onChange={(e) => handleFilter(e.target.value)}
                className="filter-select"
              >
                <option value="all">All Subjects</option>
                {stats.subjects.map(subject => (
                  <option key={subject} value={subject}>{subject}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="view-controls">
            <button 
              className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              <FaTh />
            </button>
            <button 
              className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
              onClick={() => setViewMode('list')}
            >
              <FaList />
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-section">
          <div className="loading-spinner"></div>
          <p>Loading certificates...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="error-section">
          <div className="error-content">
            <h3>Error Loading Certificates</h3>
            <p>{error}</p>
            <button onClick={() => setError(null)}>Try Again</button>
          </div>
        </div>
      )}

      {/* Certificates Grid/List */}
      {!loading && !error && (
        <>
          {filteredNfts.length === 0 ? (
            <div className="empty-state">
              <FaCertificate size={64} />
              <h3>No Certificates Found</h3>
              <p>
                {nfts.length === 0 
                  ? "This wallet doesn't have any certificates yet."
                  : "No certificates match the selected filter."
                }
              </p>
            </div>
          ) : (
            <div className={`certificates-container ${viewMode}`}>
              {filteredNfts.map((nft) => {
                const { Subject, attributes, image } = nft.metadata;
                const course = attributes?.[0]?.value || "N/A";

                return (
                  <div key={nft.tokenId} className="certificate-card">
                    <div className="certificate-image">
                      <img src={image} alt="Certificate" />
                      <div className="certificate-overlay">
                        <button 
                          className="view-btn"
                          onClick={() => setSelectedNft(nft)}
                        >
                          <FaEye /> View
                        </button>
                      </div>
                    </div>

                    <div className="certificate-content">
                      <div className="certificate-header">
                        <h3>Certificate #{nft.tokenId}</h3>
                        <div className="verified-badge">
                          <MdVerified /> Verified
                        </div>
                      </div>

                      <div className="certificate-details">
                        <div className="detail-item">
                          <FaGraduationCap />
                          <span><strong>Subject:</strong> {Subject}</span>
                        </div>
                        <div className="detail-item">
                          <FaUser />
                          <span><strong>Course:</strong> {course}</span>
                        </div>
                        <div className="detail-item">
                          <FaCalendar />
                          <span><strong>Issued:</strong> {formatDate(nft.mintDate)}</span>
                        </div>
                      </div>

                      <div className="certificate-actions">
                        <button 
                          className="action-btn primary"
                          onClick={() => setSelectedNft(nft)}
                        >
                          <FaEye /> View
                        </button>
                        <button 
                          className="action-btn secondary"
                          onClick={() => shareCertificate(nft)}
                        >
                          <FaShare /> Share
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Certificate Modal */}
      {selectedNft && (
        <div className="modal-overlay" onClick={() => setSelectedNft(null)}>
          <div className="certificate-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Certificate #{selectedNft.tokenId}</h3>
              <button 
                className="close-btn"
                onClick={() => setSelectedNft(null)}
              >
                <FaTimes />
              </button>
            </div>

            <div className="modal-content">
              <div className="certificate-preview">
                <img src={selectedNft.metadata.image} alt="Certificate" />
              </div>

              <div className="certificate-info">
                <div className="info-section">
                  <h4>Certificate Details</h4>
                  <div className="info-grid">
                    <div className="info-item">
                      <strong>Token ID:</strong>
                      <span>#{selectedNft.tokenId}</span>
                    </div>
                    <div className="info-item">
                      <strong>Subject:</strong>
                      <span>{selectedNft.metadata.Subject}</span>
                    </div>
                    <div className="info-item">
                      <strong>Course:</strong>
                      <span>{selectedNft.metadata.attributes?.[0]?.value || 'N/A'}</span>
                    </div>
                    <div className="info-item">
                      <strong>Issue Date:</strong>
                      <span>{formatDate(selectedNft.mintDate)}</span>
                    </div>
                    <div className="info-item">
                      <strong>Blockchain:</strong>
                      <span>zkSync Sepolia</span>
                    </div>
                    <div className="info-item">
                      <strong>Status:</strong>
                      <span className="verified">
                        <MdVerified /> Verified
                      </span>
                    </div>
                  </div>
                </div>

                <div className="modal-actions">
                  <button 
                    className="action-btn secondary"
                    onClick={() => shareCertificate(selectedNft)}
                  >
                    <FaShare /> Share Certificate
                  </button>
                  <button 
                    className="action-btn secondary"
                    onClick={() => window.open(`https://sepolia.explorer.zksync.io/address/${contractAddress}`, '_blank')}
                  >
                    <FaExternalLinkAlt /> View on Explorer
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NFTDashboard;