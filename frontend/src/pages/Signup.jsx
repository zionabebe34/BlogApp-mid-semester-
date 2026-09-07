import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';
import { signup } from '../api';

/**
 * Signup page. After a successful signup we send the user to the Login
 * page to sign in with their new account.
 */
function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [error, setError] = useState('');

  const handleSignup = async (e) => {
    e.preventDefault();
    if (password !== repeatPassword) {
      setError('Passwords do not match!');
      return;
    }

    try {
      await signup(name, email, password);
      navigate('/Login');
    } catch (err) {
      setError('Signup failed: ' + err.message);
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
      <Card sx={{ width: 420, p: 2 }}>
        <CardContent>
          <Typography variant="h4" sx={{ textAlign: 'center', mb: 0.5 }}>
            Join BlogApp.
          </Typography>
          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mb: 4 }}>
            Create an account to start writing.
          </Typography>

          {error && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}

          <form onSubmit={handleSignup}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Name</Typography>
            <TextField
              fullWidth
              placeholder="Your name"
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              size="small"
              sx={{ mb: 2 }}
            />

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
              sx={{ mb: 2 }}
            />

            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Repeat Password</Typography>
            <TextField
              fullWidth
              placeholder="••••••••"
              type="password"
              value={repeatPassword}
              onChange={e => setRepeatPassword(e.target.value)}
              size="small"
              sx={{ mb: 3 }}
            />

            <Button fullWidth type="submit" variant="contained" sx={{ py: 1.2, mb: 2 }}>
              Sign Up
            </Button>
          </form>

          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
            Already have an account?{' '}
            <Box
              component="span"
              onClick={() => navigate('/Login')}
              sx={{ color: 'secondary.main', cursor: 'pointer', fontWeight: 600 }}
            >
              Login
            </Box>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Signup;
