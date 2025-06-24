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
      <h1>Welcome to the show</h1>
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
