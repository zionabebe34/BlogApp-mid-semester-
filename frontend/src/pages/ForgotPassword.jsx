import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, TextField, Button } from '@mui/material';
import { forgotPassword } from '../api';

/**
 * Requests a password-reset email. The backend always answers with the same
 * generic message (whether or not the address exists) so we never learn —
 * or leak — which emails are registered.
 */
function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = await forgotPassword(email);
      setError('');
      setMessage(data.message);
    } catch (err) {
      setMessage('');
      setError(err.message || 'Something went wrong');
    }
  };

  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}>
      <Card sx={{ width: 420, p: 2 }}>
        <CardContent>
          <Typography variant="h4" sx={{ textAlign: 'center', mb: 0.5 }}>
            Reset your password.
          </Typography>
          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary', mb: 4 }}>
            Enter your email and we'll send you a reset link.
          </Typography>

          {error && (
            <Typography color="error" sx={{ mb: 2, textAlign: 'center' }}>
              {error}
            </Typography>
          )}
          {message && (
            <Typography sx={{ mb: 2, textAlign: 'center', color: 'success.main' }}>
              {message}
            </Typography>
          )}

          <form onSubmit={handleSubmit}>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>Email</Typography>
            <TextField
              fullWidth
              placeholder="you@example.com"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              size="small"
              sx={{ mb: 3 }}
            />

            <Button fullWidth type="submit" variant="contained" sx={{ py: 1.2, mb: 2 }}>
              Send reset link
            </Button>
          </form>

          <Typography variant="body2" sx={{ textAlign: 'center', color: 'text.secondary' }}>
            <Box
              component="span"
              onClick={() => navigate('/Login')}
              sx={{ color: 'secondary.main', cursor: 'pointer', fontWeight: 600 }}
            >
              Back to Login
            </Box>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default ForgotPassword;
