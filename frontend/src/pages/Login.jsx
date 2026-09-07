import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button, Divider } from '@mui/material';
import { login } from '../api';

/**
 * Login page. On success the backend sets the session cookie and we store
 * the user in App's `currentUser` state, then go to the home feed.
 */
function Login({ setCurrentUser }) {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await login(email, password);
      setCurrentUser({ email: data.email, name: data.name });
      setError('');
      navigate('/Home');
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
      <Card sx={{ width: 420, p: 2 }}>
        <CardContent>
          <Typography variant="h4" sx={{ textAlign: 'center', mb: 0.5 }}>
            Welcome back.
          </Typography>
          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mb: 4 }}>
            Sign in to keep reading and writing.
          </Typography>

          {error && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          <form onSubmit={handleLogin}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Email</Typography>
            <TextField
              fullWidth
              placeholder="you@example.com"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />

            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Password</Typography>
            <TextField
              fullWidth
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              size="small"
              sx={{ mb: 3 }}
            />

            <Button fullWidth type="submit" variant="contained" sx={{ py: 1.2, mb: 2 }}>
              Login
            </Button>
          </form>

          <Divider sx={{ mb: 2 }}>New here?</Divider>

          <Button fullWidth variant="outlined" onClick={() => navigate('/Signup')}>
            Create an account
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Login;
