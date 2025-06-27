// Home.jsx
// import { GoogleLogin } from '@react-oauth/google';
import { useGoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FaGithub, FaTwitter,FaInfoCircle } from 'react-icons/fa';
import './Home.scss';
import { MdOutlineArrowOutward } from "react-icons/md";
import { RoughNotation, RoughNotationGroup } from "react-rough-notation";
import { useEffect, useState } from 'react';
import __certimint__ from '../../video/certimint.mp4';


export default function Home() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [showAnnotation, setShowAnnotation] = useState(false);

  const googleLogin = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      try {
        const response = await fetch('https://www.googleapis.com/oauth2/v2/userinfo ', {
          headers: {
            Authorization: `Bearer ${tokenResponse.access_token}`,
          },
        });
        const userData = await response.json();

        login({
          id: userData.id,
          name: userData.name,
          email: userData.email,
          picture: userData.picture,
        });
        navigate('/upload');
      } catch (error) {
        alert('Login Failed');
      }
    },
    onError: () => {
      alert('Login Failed');
    },
  });
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowAnnotation(true);
    }, 1000); // Show after 1 second

    return () => clearTimeout(timer);
  }, []);

  function redirectToNFTDashBoard() {
    navigate('/nfts');
  }

  return (
    <div className="home-page">
      {/* Grid Background */}
      <div className="grid-background">
        <div className="grid-lines"></div>
      </div>

      {/* Login Button - Top Left */}
      <div className="login-section">
      <button
        type="button"
        className="custom-google-btn google-login-button"
        onClick={() => googleLogin()}
      >
        <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
          {/* SVG path for Google icon */}
          <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Sign in with Google
      </button>
    </div>

    {/* Top Right Circular Buttons */}
      <div className="top-right-buttons">
        <button className="circular-btn info-btn" title="Information">
          <FaInfoCircle size={20} />
        </button>
        <button onClick={redirectToNFTDashBoard} className="circular-btn arrow-btn" title="External Link">
          <MdOutlineArrowOutward size={20} />
        </button>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Header Section */}
        <div className="header-section">
          <div className="badge">
            An Analyze & Provide Remark
            <span className="look-at-me-damnit-dot look-at-me-damnit-dot--blinking roundy"></span>
          </div>
          <h1 className="main-title">
             Certify Smarter Trust {' '}
            <RoughNotation 
              type="box" 
              show={showAnnotation}
              color="#FBE9D9"
              strokeWidth={3}
              padding={8}
              animationDuration={1200}
            >
              Deeper
            </RoughNotation>
            <br />
            <span className="subtitle">Certified NFT-Secured Truly Yours.</span>
          </h1>
          <p className="description">
            Leverage the power of artificial intelligence and blockchain to issue tamper-proof, verifiable certifications. From skill assessment to lifelong proof of learning — secure, shareable, and truly owned by you.
          </p>
          
          <div className="action-buttons">
            <button className="btn-primary">Get Started</button>
            <button className="btn-secondary">Learn More</button>
          </div>
        </div>

        {/* Main Display Area */}
        <div className="display-area">
          {/* This will be filled later */}
          <video 
            className="hero-video"
            autoPlay 
            muted 
            loop 
            playsInline
          >
            <source src={__certimint__} type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>

        {/* Bottom Cards */}
        <div className="bottom-cards">
          <div className="card card-1">
            <span>div 1</span>
          </div>
          <div className="card card-2">
            <span>div 2</span>
          </div>
        </div>

        {/* Bottom Center Card */}
        <div className="center-card">
          <span>div 3</span>
        </div>
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-left">
            <p>&copy; 2025 certimint. Crafted with passion.</p>
          </div>
          <div className="footer-right">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="social-link">
              <FaGithub size={20} />
            </a>
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="social-link">
              <FaTwitter size={20} />
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
