// src/components/ProtectedRoute.jsx
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function ProtectedRoute({ children }) {
  const { user } = useAuth();

  if (!user) {
    console.log('User not authenticated, redirecting to home');
    return <Navigate to="/" />;
  }else{
    console.log(user);
    console.log('User authenticated, rendering protected route');
  }

  return children;
}
