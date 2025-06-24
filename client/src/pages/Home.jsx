// Home.jsx
import { GoogleLogin } from '@react-oauth/google';
import { jwtDecode } from 'jwt-decode';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Home() {
  const navigate = useNavigate();
  const { login } = useAuth();

  return (
    <div>
      <div className="welcome-alert" style={{ textAlign: 'center', marginTop: '50px' }}>
        <h1>Welcome to the show</h1>
        <p>
          This website is currently under development. You can log in using your Google account to access the upload page. But the rest of the features are not yet implemented but will be available in 1-2 days.
        </p>
      </div>
      <GoogleLogin
        onSuccess={credentialResponse => {
          const decoded = jwtDecode(credentialResponse.credential);
          const userData = {
            id: decoded.sub,
            name: decoded.name,
            email: decoded.email,
            picture: decoded.picture,
          };
          login(userData);
          navigate('/upload');
        }}
        onError={() => {
          alert('Login Failed');
        }}
      />
    </div>
  );
}
